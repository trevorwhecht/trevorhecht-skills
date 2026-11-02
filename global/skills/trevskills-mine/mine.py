#!/usr/bin/env python3
"""List, rank and read interactive Claude Code chats that are new since the last mining run.

usage: mine.py candidates [--days 14] [--exclude S]   one condensed line per new session
       mine.py rank [--top 20] [--min 0.5] [--days 14] [--exclude S]   Jev-ranked lines, then "MARK <epoch>"
       mine.py text <path>                             typed text of one transcript, "<role>: <text>" lines
       mine.py mark <epoch>                            move the last-mined marker
Headless (sdk-cli) sessions and subagent transcripts are skipped. Stdlib only.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
MARKER = Path.home() / ".claude" / "transcript-mining" / "last-mined"
JEV = Path.home() / ".claude" / "scripts" / "jev-rank.py"
QUESTIONS = [
    "This chat ends with work that was planned or started but not finished",
    "In this chat the user taught a fact, rule or process that should be saved to a doc",
    "In this chat a finding or problem was noticed and then dropped without being fixed or tracked",
]
LINE_MAX = 1500  # jev-rank's MAX_CHARS
MSG_MAX, TOTAL_MAX, HEAD, TAIL = 2000, 40000, 10000, 30000
SKIP_PREFIXES = ("Base directory for this skill", "<command-message>", "<command-name>")


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
    return " ".join(c["text"] for c in content
                    if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str))


def typed(path):
    """Yield (role, text, record) for typed user/assistant text only."""
    for d in records(path):
        m = d.get("message")
        if not isinstance(m, dict) or d.get("isMeta"):
            continue
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        t = " ".join(text_of(m.get("content")).split())
        if t and not t.startswith(SKIP_PREFIXES):
            yield role, t, d


def messages(path):
    for role, t, _ in typed(path):
        yield role, t


def candidate_line(path):
    """Condensed one-line summary, or None for a headless session or one with no typed text."""
    cwd = day = entry = None
    users, last = [], ""
    for d in records(path):
        entry = entry or d.get("entrypoint")
        cwd = cwd or d.get("cwd")
    if entry == "sdk-cli":
        return None
    for role, t, d in typed(path):
        day = day or str(d.get("timestamp", ""))[:10] or None
        if role == "user":
            users.append(t)
        else:
            last = t
    if not users and not last:
        return None
    day = day or time.strftime("%Y-%m-%d", time.localtime(path.stat().st_mtime))
    body = f"U: {' '.join(users)[:700]} || END: {last[-600:]}"
    rest = " ".join(f"{day} | {cwd or '?'} | {path.stem[:8]} | {body}".split())
    return f"{' '.join(str(path).split())}\t{rest}"[:LINE_MAX]


def find(days, exclude):
    """[(mtime, line)] for new interactive sessions, oldest first."""
    try:
        since = float(MARKER.read_text().strip())
        new = lambda m: int(m) > since  # whole seconds: `stat -f %m` and MARK both floor
    except (OSError, ValueError):
        cutoff = time.time() - days * 86400
        new = lambda m: m >= cutoff
    out = []
    for p in ROOT.rglob("*.jsonl"):
        s = str(p)
        if "/subagents/" in s or (exclude and exclude in s):
            continue
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if new(m):
            line = candidate_line(p)
            if line:
                out.append((m, line))
    return sorted(out)


def rank(a):
    found = find(a.days, a.exclude)
    if not found:
        print("mine: no new sessions")
        return 0
    lines = [l for _, l in found]
    best = {}
    for q in QUESTIONS:
        try:
            if not JEV.is_file():
                raise RuntimeError(f"{JEV} not found")
            r = subprocess.run([sys.executable, str(JEV), q, "--top", "1000"],
                               input="\n".join(lines) + "\n", capture_output=True, text=True)
        except (OSError, RuntimeError) as e:
            return fail(str(e))
        if r.returncode:
            err = r.stderr.strip().splitlines()
            return fail(err[-1] if err else f"exit {r.returncode}")
        for row in r.stdout.splitlines():
            score, _, line = row.partition("\t")
            try:
                s = float(score)
            except ValueError:
                continue
            if line and s > best.get(line, -1):
                best[line] = s
    ranked = sorted(((s, l) for l, s in best.items() if s >= a.min), key=lambda x: -x[0])
    for s, l in ranked[:a.top]:
        print(f"{s:.2f}\t{l}")
    print(f"MARK {int(found[-1][0])}")
    return 0


def fail(reason):
    print(f"mine: jev-rank failed: {reason}", file=sys.stderr)
    return 1


def text(path):
    out = "\n".join(f"{role}: {t[:MSG_MAX]}" for role, t in messages(path))
    if len(out) > TOTAL_MAX:
        out = f"{out[:HEAD]}\n[... cut ...]\n{out[-TAIL:]}"
    if out:
        print(out)
    return 0


def mark(epoch):
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(f"{epoch}\n")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("candidates", "rank"):
        s = sub.add_parser(name)
        s.add_argument("--days", type=int, default=14)
        s.add_argument("--exclude", default="", help="session id to skip (the current one)")
        if name == "rank":
            s.add_argument("--top", type=int, default=20)
            s.add_argument("--min", type=float, default=0.5)
    sub.add_parser("text").add_argument("path", type=Path)
    sub.add_parser("mark").add_argument("epoch", type=lambda v: int(float(v)))
    a = p.parse_args()
    if a.cmd == "candidates":
        for _, line in find(a.days, a.exclude):
            print(line)
        return 0
    if a.cmd == "rank":
        return rank(a)
    if a.cmd == "text":
        return text(a.path)
    return mark(a.epoch)


if __name__ == "__main__":
    sys.exit(main())
