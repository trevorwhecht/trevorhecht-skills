#!/usr/bin/env bash
#
# scan.sh: static NVIDIA SkillSpector scan of Claude Code skills, agents and plugins.
# Read-only: it never uninstalls, moves or edits anything it scans.
#
#   scan.sh                  every installed skill, agent and plugin under ~/.claude and ~/.claude-owa
#   scan.sh <path | git URL> one skill, plugin or agent, before it is installed
#
# Writes ~/Developer/claude/skill-scans/<date>.md, worst first, and prints the do-not-install names.
# Exit: 0 nothing flagged, 1 something is DO_NOT_INSTALL, 2 a scan failed or bad usage.
set -euo pipefail

usage() { echo "usage: scan.sh [path | git URL]" >&2; exit 2; }
[ $# -le 1 ] || usage
case "${1:-}" in -*) usage ;; esac

SS_VERSION=2.13.6
SS_COMMIT=e2674da339b0bddc6e565d059c0577c6d9cd25da  # tag v2.13.6; a tag can move, a commit cannot

command -v uv >/dev/null || { echo "scan.sh needs uv: brew install uv" >&2; exit 2; }
SS="$(uv tool dir --bin)/skillspector"
if [ "$("$SS" --version 2>/dev/null || true)" != "SkillSpector v$SS_VERSION" ]; then
  # Python 3.12: yara-python ships prebuilt wheels for 3.12 and 3.13 only.
  uv tool install --force --python 3.12 \
    "skillspector @ git+https://github.com/NVIDIA/skillspector.git@$SS_COMMIT" >&2
fi

exec python3 - "$SS" "$@" <<'PY'
import concurrent.futures as cf, json, os, re, subprocess, sys

SS, args = sys.argv[1], sys.argv[2:]
HOME = os.path.expanduser("~")
GIT_URL = re.compile(r"^(https?|ssh|git)://|^git@")


def walk(top):
    """os.walk that follows symlinks, visits each real folder once and skips hidden folders."""
    seen = set()
    for d, dirs, files in os.walk(top, followlinks=True):
        real = os.path.realpath(d)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "node_modules"]
        yield d, dirs, files


def installed():
    """{real path: (kind, name)} for every skill, agent and plugin on both accounts."""
    found = {}
    for root in (os.path.join(HOME, ".claude"), os.path.join(HOME, ".claude-owa")):
        for d, dirs, files in walk(os.path.join(root, "skills")):
            if "SKILL.md" in files:
                found.setdefault(os.path.realpath(d), ("skill", os.path.basename(d)))
                dirs[:] = []  # a skill is scanned whole, nested folders included
        for d, _, files in walk(os.path.join(root, "agents")):
            for f in files:
                p = os.path.join(d, f)
                if f.endswith(".md") and os.path.isfile(p):
                    found.setdefault(os.path.realpath(p), ("agent", f[:-3]))
        try:
            with open(os.path.join(root, "plugins", "installed_plugins.json")) as fh:
                plugins = json.load(fh).get("plugins", {})
        except (OSError, ValueError):
            plugins = {}
        for name, entries in plugins.items():
            for entry in entries:
                p = entry.get("installPath") or ""
                if os.path.isdir(p):
                    found.setdefault(os.path.realpath(p), ("plugin", name))
    return found


def scan(target):
    """SkillSpector's static pass only (--no-llm: no LLM, no API key). Returns (report, error)."""
    try:
        r = subprocess.run([SS, "scan", "--no-llm", "--format", "json", "--", target],
                           capture_output=True, text=True, timeout=1500)
        return json.loads(r.stdout), None
    except subprocess.TimeoutExpired:
        return None, "timed out after 25 minutes"
    except ValueError:
        return None, " ".join(r.stderr.split()) or f"skillspector exit {r.returncode}"


def given(arg):
    """The one path or git URL to scan before it is installed."""
    if GIT_URL.match(arg):
        return {arg: ("git URL", re.sub(r"\.git$", "", arg.rstrip("/")).rsplit("/", 1)[-1])}
    if not os.path.exists(arg):
        print(f"scan.sh: no such path, and not a git URL: {arg}", file=sys.stderr)
        sys.exit(2)
    real = os.path.realpath(arg)  # SkillSpector refuses a symlinked input
    return {real: ("path", os.path.basename(real))}


targets = given(args[0]) if args else installed()
with cf.ThreadPoolExecutor(max_workers=4) as pool:
    results = dict(zip(targets, pool.map(scan, targets)))
PY
