#!/usr/bin/env python3
"""List, rank and read interactive Claude Code chats that are new since the last mining run.

usage: mine.py candidates [--days 14] [--exclude S]   one condensed line per new session
       mine.py rank [--top 20] [--min 0.5] [--days 14] [--exclude S]   Jev-ranked lines, then "MARK <epoch>"
       mine.py text <path>                             typed text of one transcript, "<role>: <text>" lines
       mine.py mark <epoch>                            move the last-mined marker
       mine.py archive [--days 30] [--remote R] [--apply]   mined sessions older than --days -> R as .jsonl.xz
                                                       (dry run unless --apply; --apply needs rclone)
Headless (sdk-cli) sessions and subagent transcripts are skipped. Stdlib only.
"""
import argparse, hashlib, json, lzma, re, shutil, subprocess, sys, tempfile, time
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


def digest(path, algo, opener=open):
    h = hashlib.new(algo)
    with opener(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def rclone(*args):
    r = subprocess.run(["rclone", *args], capture_output=True, text=True)
    if r.returncode:
        err = r.stderr.strip().splitlines()
        raise RuntimeError(f"rclone {args[0]} exit {r.returncode}" + (f": {err[-1]}" if err else ""))
    return r.stdout


def archivable(days):
    """[(path, stat)] of top-level interactive sessions (and subagent transcripts of archived ones) at or before the marker and older than `days`, or None."""
    try:
        since = float(MARKER.read_text().strip())
    except (OSError, ValueError):
        return None
    cutoff = time.time() - days * 86400
    out = []
    for p in sorted(ROOT.glob("*/*.jsonl")):  # top-level sessions
        try:
            st = p.stat()
        except OSError:
            continue
        if not p.is_symlink() and int(st.st_mtime) <= since and st.st_mtime < cutoff and candidate_line(p):
            out.append((p, st))
    # subagent transcripts, only once their session file is gone (already archived)
    for p in sorted(ROOT.glob("*/*/subagents/*.jsonl")):
        try:
            st = p.stat()
        except OSError:
            continue
        if (not p.is_symlink() and not p.parents[1].with_suffix(".jsonl").exists()
                and int(st.st_mtime) <= since and st.st_mtime < cutoff):
            out.append((p, st))
    return out


def archive_one(p, st, dst, tmp):
    """Compress, round-trip, upload, verify size+md5, then delete. Raises on any failed step."""
    xz = Path(tmp) / "upload.jsonl.xz"
    try:
        with open(p, "rb") as src, lzma.open(xz, "wb") as out:
            while chunk := src.read(1 << 20):
                out.write(chunk)
        if digest(xz, "sha256", lzma.open) != digest(p, "sha256"):
            raise RuntimeError("xz round-trip hash differs")
        size, md5 = xz.stat().st_size, digest(xz, "md5")
        rclone("copyto", "--", str(xz), dst)
        entries = json.loads(rclone("lsjson", "--hash", "--", dst))
        if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
            raise RuntimeError(f"lsjson returned {len(entries) if isinstance(entries, list) else 'no'} entries")
        e = entries[0]
        if e.get("Size") != size:
            raise RuntimeError(f"remote size {e.get('Size')} != local {size}")
        remote_md5 = (e.get("Hashes") or {}).get("md5")
        if not remote_md5 or str(remote_md5).lower() != md5:
            raise RuntimeError(f"remote md5 {remote_md5 or 'missing'} != local {md5}")
        now = p.stat()
        if (now.st_mtime, now.st_size) != (st.st_mtime, st.st_size):
            raise RuntimeError("source changed during the run")
        p.unlink()
    finally:
        xz.unlink(missing_ok=True)


def archive(a):
    remote = a.remote.rstrip("/")
    name = remote.partition(":")[0]
    if a.apply:
        if shutil.which("rclone") is None:
            print("mine: rclone not found, nothing archived", file=sys.stderr)
            return 1
        try:
            names = rclone("listremotes").split()
        except (OSError, RuntimeError):
            names = []
        if ":" not in remote or remote.startswith("-") or f"{name}:" not in names:
            print(f"mine: rclone remote {name}: not configured, nothing archived", file=sys.stderr)
            return 1
    found = archivable(a.days)
    if found is None:
        print("mine: no last-mined marker, nothing to archive")
        return 0
    if not found:
        print("mine: nothing to archive")
        return 0
    dst = lambda p: f"{remote}/{p.relative_to(ROOT).as_posix()}.xz"
    if not a.apply:
        for p, _ in found:
            print(f"would archive {p} -> {dst(p)}")
        print(f"mine: {len(found)} to archive, {sum(st.st_size for _, st in found)} bytes (dry run)")
        return 0
    rc = 0
    with tempfile.TemporaryDirectory(prefix="mine-archive-") as tmp:
        for p, st in found:
            try:
                archive_one(p, st, dst(p), tmp)
                print(f"archived {p}")
            except (OSError, RuntimeError, ValueError, lzma.LZMAError) as e:
                print(f"kept {p}: {e}")
                rc = 1
    return rc


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
    s.add_argument("--remote", default="gdrive:claude-transcripts")
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
        return archive(a)
    return mark(a.epoch)


if __name__ == "__main__":
    sys.exit(main())
