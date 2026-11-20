#!/usr/bin/env bash
#
# scan.sh: static NVIDIA SkillSpector scan of Claude Code skills, agents, commands and plugins.
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

exec python3 - "$SS" "$SS_VERSION" "$@" <<'PY'
import concurrent.futures as cf, datetime, json, os, re, subprocess, sys

SS, VERSION, args = sys.argv[1], sys.argv[2], sys.argv[3:]
HOME = os.path.expanduser("~")
GIT_URL = re.compile(r"^(https?|ssh|git)://|^git@")
SEVERITY = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
WORST = {"DO_NOT_INSTALL": 0, "SCAN FAILED": 1, "CAUTION": 2, "SAFE": 3}


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
    """{real path: (kind, name)} for every skill, agent, command and plugin on both accounts."""
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
        for d, _, files in walk(os.path.join(root, "commands")):
            for f in files:
                p = os.path.join(d, f)
                if f.endswith(".md") and os.path.isfile(p):
                    found.setdefault(os.path.realpath(p), ("command", f[:-3]))
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


def cell(text):
    return " ".join(str(text).split()).replace("|", "\\|")


def short(p):
    for h in (HOME, os.path.realpath(HOME)):
        if p.startswith(h + "/"):
            return "~" + p[len(h):]
    return p


def top_findings(issues, n=3):
    """The n worst distinct findings: severity, rule, pattern, file:line and the matched text."""
    picked, keys = [], set()
    for i in sorted(issues, key=lambda i: (SEVERITY.get(i.get("severity"), 9), -(i.get("confidence") or 0))):
        key = (i.get("id"), cell(i.get("finding", "")))
        if key not in keys and len(picked) < n:
            keys.add(key)
            loc = i.get("location") or {}
            match = cell(i.get("finding", "")).replace("`", "'")
            match = match if len(match) <= 60 else match[:60] + "…"
            picked.append(f"{i.get('severity')} {i.get('id')} {cell(i.get('pattern', ''))}, "
                          f"{cell(loc.get('file', '?'))}:{loc.get('start_line', '?')}: `{match}`")
    more = len(issues) - len(picked)
    return "<br>".join(picked + ([f"+{more} more"] if more > 0 else []))


def result(path, kind, name, report, error):
    """One report row's fields from one SkillSpector JSON report (or its error)."""
    r = {"name": name, "kind": kind, "path": short(path), "score": "-", "verdict": "SCAN FAILED", "top": cell(error or "")}
    if not error and report.get("execution_successful") is False:
        error = "SkillSpector reported execution_successful false"
        r["top"] = error
    if not error:
        risk = report.get("risk_assessment", {})
        partial = (report.get("analysis_completeness") or {}).get("status", "complete") != "complete"
        r.update(score=risk.get("score", 0), verdict=risk.get("recommendation", "?"),
                 shown=risk.get("recommendation", "?") + (" (partial)" if partial else ""),
                 top=top_findings(report.get("issues", [])))
    return r


targets = given(args[0]) if args else installed()
results = []
with cf.ThreadPoolExecutor(max_workers=4) as pool:
    jobs = {pool.submit(scan, p): p for p in targets}
    for n, job in enumerate(cf.as_completed(jobs), 1):
        r = result(jobs[job], *targets[jobs[job]], *job.result())
        results.append(r)
        print(f"[{n}/{len(targets)}] {r['verdict']} {r['score']} {r['name']}", file=sys.stderr)
results.sort(key=lambda r: (WORST.get(r["verdict"], 1), -(r["score"] if r["score"] != "-" else 0), r["name"]))
hits = lambda verdict: [r for r in results if r["verdict"] == verdict]

today = datetime.date.today().isoformat()
out_dir = os.path.join(HOME, "Developer", "claude", "skill-scans")
os.makedirs(out_dir, exist_ok=True)
# A one-target scan gets its own file so it never replaces the day's full scan.
suffix = "-" + re.sub(r"[^A-Za-z0-9._-]", "-", results[0]["name"]) if args else ""
out = os.path.join(out_dir, f"{today}{suffix}.md")
with open(out, "w") as fh:
    fh.write(f"# Skill scan {today}{' of ' + args[0] if args else ''}\n\n"
             f"SkillSpector {VERSION}, static pass only (`--no-llm`: no LLM, no API key). {len(results)} scanned: "
             f"{len(hits('DO_NOT_INSTALL'))} do not install, {len(hits('CAUTION'))} caution, "
             f"{len(hits('SAFE'))} safe, {len(hits('SCAN FAILED'))} failed. Nothing was uninstalled or edited.\n"
             "Full detail for one row: `skillspector scan --no-llm <path>`.\n\n"
             "| Name | Kind | Path | Score | Verdict | Top findings |\n|---|---|---|---|---|---|\n")
    for r in results:
        fh.write(f"| {cell(r['name'])} | {r['kind']} | `{cell(r['path'])}` | {r['score']} | "
                 f"{r.get('shown', r['verdict'])} | {r['top']} |\n")

print(f"Report: {short(out)}")
for label, verdict in (("Do not install", "DO_NOT_INSTALL"), ("Scan failed", "SCAN FAILED")):
    if hits(verdict) or verdict == "DO_NOT_INSTALL":
        print(f"{label} ({len(hits(verdict))}):" + "".join(f"\n  {r['name']}  {r['path']}" for r in hits(verdict)))
sys.exit(2 if hits("SCAN FAILED") else 1 if hits("DO_NOT_INSTALL") else 0)
PY
