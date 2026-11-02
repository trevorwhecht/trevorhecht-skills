#!/usr/bin/env python3
"""List, rank and read interactive Claude Code chats that are new since the last mining run.

usage: mine.py candidates [--days 14] [--exclude S]   one condensed line per new session
       mine.py rank [--top 20] [--min 0.5] [--days 14] [--exclude S]   Jev-ranked lines, then "MARK <epoch>"
       mine.py text <path>                             typed text of one transcript, "<role>: <text>" lines
       mine.py mark <epoch>                            move the last-mined marker
       mine.py archive [--days 30] [--dest DIR] [--apply]   xz mined .jsonl older than --days into Google Drive
Headless (sdk-cli) sessions and subagent transcripts are skipped. Stdlib only.
"""
import argparse, json, lzma, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
MARKER = Path.home() / ".claude" / "transcript-mining" / "last-mined"
CLOUD = Path.home() / "Library" / "CloudStorage"
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


SCRUM_START = re.compile(r"^(<command-message>.*?</command-message>\s*)?(<command-name>)?/trevskills-scrum")


def scrum_started(path):
    """True when the first typed user record is a /trevskills-scrum prompt (headless job sessions)."""
    for d in records(path):
        m = d.get("message")
        if isinstance(m, dict) and m.get("role") == "user" and not d.get("isMeta"):
            t = " ".join(text_of(m.get("content")).split())
            if t:
                return bool(SCRUM_START.match(t))
    return False


def candidate_line(path):
    """Condensed one-line summary, or None for a headless session or one with no typed text."""
    cwd = day = entry = None
    users, last = [], ""
    for d in records(path):
        entry = entry or d.get("entrypoint")
        cwd = cwd or d.get("cwd")
    if entry == "sdk-cli" or scrum_started(path):
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


def drive_dest():
    """<first GoogleDrive-*/My Drive by name>/claude-transcript-archive, or None."""
    hits = sorted(CLOUD.glob("GoogleDrive-*/My Drive"))
    return hits[0] / "claude-transcript-archive" if hits else None


def same_xz(xz_path, orig):
    """True when xz_path decompresses to exactly the bytes of orig (streamed in 1 MiB chunks)."""
    with lzma.open(xz_path, "rb") as a, open(orig, "rb") as b:
        while True:
            x, y = a.read(1 << 20), b.read(1 << 20)
            if x != y:
                return False
            if not x:
                return True


def archive(dest, days, apply):
    """xz-compress mined .jsonl files older than `days` into dest/<rel>.xz, verify, then remove the original."""
    dest = dest or drive_dest()
    if dest is None:
        print("mine: no Google Drive folder, archive skipped")
        return 0
    try:
        since = float(MARKER.read_text().strip())
    except (OSError, ValueError):
        print("mine: no last-mined marker, archive skipped")
        return 0
    cutoff = time.time() - days * 86400
    picked = []
    for p in sorted(ROOT.rglob("*.jsonl")):
        rel = p.relative_to(ROOT)
        if "memory" in rel.parts[:-1] or p.is_symlink() or not p.is_file():
            continue
        try:
            st = p.stat()
        except OSError:
            continue
        if int(st.st_mtime) <= since and st.st_mtime <= cutoff:  # whole seconds, as in find()
            picked.append((p, rel, st.st_size))
    if not apply:
        for p, _, size in picked:
            print(f"{size}\t{p}")
        print(f"{len(picked)} file(s)")
        return 0
    done = kept = 0
    for p, rel, _ in picked:
        target = dest / f"{rel}.xz"
        tmp = target.with_name(target.name + ".tmp")
        reason = None
        if target.exists():
            reason = "archive exists"
        else:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "rb") as src, lzma.open(tmp, "wb") as out:
                    while chunk := src.read(1 << 20):
                        out.write(chunk)
                if not same_xz(tmp, p):
                    reason = "verify failed"
                else:
                    os.rename(tmp, target)
                    p.unlink()
            except (OSError, lzma.LZMAError) as e:
                reason = str(e) or type(e).__name__
            finally:
                tmp.unlink(missing_ok=True)
        if reason:
            kept += 1
            print(f"KEPT ({reason}) {p}")
        else:
            done += 1
            print(f"archived {p} -> {target}")
    print(f"mine: {done} archived, {kept} kept")
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
    s = sub.add_parser("archive")
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--dest", type=Path)
    s.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.cmd == "candidates":
        for _, line in find(a.days, a.exclude):
            print(line)
        return 0
    if a.cmd == "rank":
        return rank(a)
    if a.cmd == "text":
        return text(a.path)
    if a.cmd == "archive":
        return archive(a.dest, a.days, a.apply)
    return mark(a.epoch)


if __name__ == "__main__":
    sys.exit(main())
