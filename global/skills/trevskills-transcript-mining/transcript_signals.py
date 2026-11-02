#!/usr/bin/env python3
"""Process signals from headless scrum transcripts, for the scrum digest.

usage: transcript_signals.py [--projects-dir DIR] [--days 7] [--out FILE] [--top 5] [--jev PATH] [--no-jev]

Reads Claude Code transcripts changed in the last N days. For each headless scrum session
(orchestrator) and its subagents it counts turns, tokens, wall time, tool-call loops, repeated
failing commands, re-reads, stuck agents and orchestrator retries, all in code. Outliers alone go
to Jev ("did this agent flail?"). Scrum complaints from interactive chats are collected too.
Writes transcript-signals.md (default: <trevskills-scrum repo>/scrum/digests/). Stdlib only.
"""
import argparse, json, os, re, statistics, subprocess, sys, tempfile, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Thresholds: starting values, tune here.
LOOP_MIN = 5          # identical (tool, input) calls
FAIL_MIN = 2          # same Bash command failing
REREAD_MIN = 6        # same file Read
RETRY_MIN = 2         # same (subagent_type, description) spawned by the orchestrator
MEDIAN_X = 3          # turns/tokens/wall above this multiple of the role median...
FLOOR = {"turns": 30, "tokens": 2_000_000, "wall_s": 900}  # ...and above this absolute floor
MEDIAN_MIN_SESSIONS = 3
COMPLAINT_CUT = 200
FLAIL_Q = "this agent flailed: looped, retried the same failing step, or stalled without progress"
COMPLAINT_Q = "Trevor is complaining about or correcting how the scrum pipeline behaves"
SIGNALS = ("loops", "failing_cmds", "rereads", "retries")
SECTIONS = ("Per role", "Outliers", "Top flails", "Trevor about scrum")


def records(path):
    """Yield each JSON object in a .jsonl file; malformed lines are skipped."""
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    yield d
    except OSError:
        return


def text_of(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return " ".join(c.get("text", "") for c in content
                    if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str))


def blocks(d):
    m = d.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def scrum_job(path):
    """Job id when the first user record is a /trevskills-scrum command, '' for a job-less one, else None."""
    for d in records(path):
        if d.get("type") != "user":
            continue
        m = d.get("message")
        t = text_of(m.get("content") if isinstance(m, dict) else None)
        if "<command-name>/trevskills-scrum</command-name>" not in t:
            return None
        args = re.search(r"<command-args>(.*?)</command-args>", t, re.S)
        words = args.group(1).split() if args else []
        return words[1] if len(words) > 1 else ""
    return None


def find_sessions(projects_dir, days):
    cutoff = time.time() - days * 86400
    recent = lambda p: p.stat().st_mtime >= cutoff
    out = []
    for top in sorted(Path(projects_dir).glob("*/*.jsonl")):
        try:
            if not recent(top):
                continue
        except OSError:
            continue
        job = scrum_job(top)
        if job is None:
            out.append({"path": top, "kind": "interactive", "job": None, "role": None})
            continue
        out.append({"path": top, "kind": "scrum", "job": job, "role": "orchestrator"})
        for sub in sorted((top.parent / top.stem / "subagents").glob("agent-*.jsonl")):
            try:
                if not recent(sub):
                    continue
                role = json.loads(sub.with_name(sub.stem + ".meta.json").read_text()).get("agentType") or "unknown"
            except OSError:
                if not sub.exists():
                    continue
                role = "unknown"
            except (ValueError, AttributeError):
                role = "unknown"
            out.append({"path": sub, "kind": "scrum", "job": job, "role": str(role)})
    return out


def parse_ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def session_stats(path, role=""):
    usage, stamps, uses, failed = {}, [], {}, Counter()
    for d in records(path):
        t = parse_ts(d.get("timestamp")) if d.get("timestamp") else None
        if t is not None:
            stamps.append(t)
        if d.get("type") == "assistant":
            m = d.get("message") or {}
            if isinstance(m, dict) and m.get("id"):
                u = m.get("usage") if isinstance(m.get("usage"), dict) else {}
                usage[m["id"]] = sum(v for k in ("input_tokens", "cache_creation_input_tokens",
                                                 "cache_read_input_tokens", "output_tokens")
                                     if isinstance(v := u.get(k), (int, float)))
            for b in blocks(d):
                if b.get("type") == "tool_use":
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    uses[b.get("id") or f"_{len(uses)}"] = (str(b.get("name")), inp)
        elif d.get("type") == "user":
            for b in blocks(d):
                if b.get("type") == "tool_result" and b.get("is_error") is True:
                    failed[b.get("tool_use_id")] += 1
    calls = list(uses.values())
    over = lambda counter, n: sum(1 for v in counter.values() if v >= n)
    fails = Counter()
    for tid, n in failed.items():
        name, inp = uses.get(tid, ("", {}))
        if name == "Bash":
            fails[str(inp.get("command"))] += n
    return {
        "turns": len(usage),
        "tokens": int(sum(usage.values())),
        "wall_s": int(max(stamps) - min(stamps)) if stamps else 0,
        "loops": over(Counter((n, json.dumps(i, sort_keys=True)) for n, i in calls), LOOP_MIN),
        "failing_cmds": over(fails, FAIL_MIN),
        "rereads": over(Counter(str(i.get("file_path")) for n, i in calls if n == "Read"), REREAD_MIN),
        "stuck": role.startswith("scrum-") and not any(
            n in ("Write", "Edit") and str(i.get("file_path", "")).endswith(".md") for n, i in calls),
        "retries": over(Counter((str(i.get("subagent_type")), str(i.get("description")))
                                for n, i in calls if n in ("Agent", "Task")), RETRY_MIN)
        if role == "orchestrator" else 0,
    }


def find_outliers(stats):
    by_role = {}
    for s in stats:
        by_role.setdefault(s["role"], []).append(s)
    out = []
    for s in stats:
        peers = by_role[s["role"]]
        big = []
        if len(peers) >= MEDIAN_MIN_SESSIONS:
            for k in ("turns", "tokens", "wall_s"):
                med = statistics.median(p[k] for p in peers)
                if s[k] > MEDIAN_X * med and s[k] > FLOOR[k]:
                    big.append(k)
        if big or s["stuck"] or any(s[k] > 0 for k in SIGNALS):
            out.append(dict(s, big=big))
    return out


def signal_count(o):
    return sum(o[k] for k in SIGNALS) + int(o["stuck"]) + len(o.get("big", []))


def signals_text(o):
    parts = [f"{k} {o[k]}" for k in SIGNALS if o[k]]
    if o["stuck"]:
        parts.append("stuck")
    parts += [f"{k}>{MEDIAN_X}x median" for k in o.get("big", [])]
    return ", ".join(parts)


def outlier_line(o):
    return f"{o['job'] or '?'} · {o['role']} · {signals_text(o)} — {o['path']}"


def jev_rank(lines, query, top, jev, min_score=0.0):
    """[(score, line)] best first, or None when Jev is unavailable."""
    if not Path(jev).is_file():
        return None
    try:
        r = subprocess.run([sys.executable, str(jev), query, "--top", str(top), "--min", str(min_score)],
                           input="\n".join(lines) + "\n", capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode:
        return None
    out = []
    for row in r.stdout.splitlines():
        score, _, line = row.partition("\t")
        try:
            out.append((float(score), line))
        except ValueError:
            continue
    return out


def complaints(path):
    """Plain-string user messages Trevor typed that mention scrum."""
    for d in records(path):
        m = d.get("message")
        if (d.get("type") != "user" or d.get("isMeta") or d.get("isCompactSummary")
                or d.get("entrypoint") == "sdk-cli" or not isinstance(m, dict)):
            continue  # sdk-cli: a script's prompt, not typed text
        c = m.get("content")
        # "<..." strings are slash-command and system wrappers, not typed text
        if isinstance(c, str) and "scrum" in c.lower() and not c.lstrip().startswith("<"):
            yield " ".join(c.split())


def fmt_secs(s):
    s = int(s)
    return f"{s // 3600}h{s % 3600 // 60:02d}m" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"


def cut(text, n=COMPLAINT_CUT):
    return text if len(text) <= n else text[:n] + "…"


def render(days, stats, n_interactive, outliers, flails, said, jev_ok):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    head = (f"# Transcript signals\nGenerated: {now} · window: {days} days · scrum sessions: {len(stats)} · "
            f"interactive sessions: {n_interactive} · Jev: {'ok' if jev_ok else 'unavailable'}\n")
    roles = {}
    for s in stats:
        roles.setdefault(s["role"], []).append(s)
    med = lambda ss, k: statistics.median(s[k] for s in ss)
    table = ["| role | sessions | median turns | median tokens | median wall |", "|---|---|---|---|---|"]
    table += [f"| {r} | {len(ss)} | {med(ss, 'turns'):g} | {med(ss, 'tokens'):.0f} | {fmt_secs(med(ss, 'wall_s'))} |"
              for r, ss in sorted(roles.items())]
    body = {
        "Per role": table if stats else [],
        "Outliers": [f"- {outlier_line(o)}" for o in outliers],
        "Top flails": [f"- {'—' if s is None else f'{s:.2f}'} · {l}" for s, l in flails],
        "Trevor about scrum": [f"- {cut(t)} — {p}" for t, p in said],
    }
    return head + "".join(f"\n## {h}\n" + ("\n".join(body[h]) or "None") + "\n" for h in SECTIONS)


def default_out():
    reg = Path.home() / ".claude" / "trevskills-scrum" / "projects.json"
    try:
        entries = json.loads(reg.read_text())
    except (OSError, ValueError):
        return None
    for e in entries if isinstance(entries, list) else []:
        if isinstance(e, str) and Path(e).name == "trevskills-scrum":
            return Path(e) / "scrum" / "digests" / "transcript-signals.md"
    return None


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".transcript-signals.")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv=None):
    home = Path.home() / ".claude"
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projects-dir", type=Path, default=home / "projects")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--out", type=Path)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--jev", type=Path, default=home / "scripts" / "jev-rank.py")
    p.add_argument("--no-jev", action="store_true")
    a = p.parse_args(argv)
    out = a.out or default_out()
    if out is None:
        print("transcript_signals: no trevskills-scrum project registered; pass --out", file=sys.stderr)
        return 2

    sessions = find_sessions(a.projects_dir, a.days)
    stats = [dict(s, **session_stats(s["path"], s["role"])) for s in sessions if s["kind"] == "scrum"]
    interactive = [s for s in sessions if s["kind"] == "interactive"]
    outliers = sorted(find_outliers(stats), key=lambda o: (-signal_count(o), -o["tokens"]))
    jev_ok = not a.no_jev and a.jev.is_file()

    flails = []
    if outliers:
        ranked = jev_rank([outlier_line(o) for o in outliers], FLAIL_Q, a.top, a.jev) if jev_ok else None
        if ranked is None:
            jev_ok = False
            flails = [(None, outlier_line(o)) for o in outliers[:a.top]]
        else:
            flails = ranked

    cands = [(t, s["path"]) for s in interactive for t in complaints(s["path"])]
    said = cands
    if cands and jev_ok:
        lines = {f"{cut(t, 1200)} — {p}": (t, p) for t, p in cands}
        ranked = jev_rank(list(lines), COMPLAINT_Q, 10, a.jev, 0.5)
        if ranked is None:
            jev_ok = False
        else:
            said = [lines[l] for _, l in ranked if l in lines]

    write_atomic(out, render(a.days, stats, len(interactive), outliers, flails, said, jev_ok))
    print(f"transcript_signals: wrote {out} ({len(stats)} scrum, {len(outliers)} outliers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
