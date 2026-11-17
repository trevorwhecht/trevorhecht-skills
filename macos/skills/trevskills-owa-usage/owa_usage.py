#!/usr/bin/env python3
"""OWA Claude account usage split between two Macs. Stdlib only, runs on Python 3.9.

  count --since ISO --until ISO [--owa-only]   JSON token totals for [since, until)
  week [--now ISO]                             current OWA week per Mac
  report [--now ISO]                           upsert the week row in iCloud Drive
  install                                      write and load the hourly LaunchAgent
"""
import argparse
import datetime as dt
import json
import os
import plistlib
import socket
import subprocess
import sys
from pathlib import Path

PLAN_USD = 200
WEIGHTS = {"input": 1, "output": 5, "cache_write": 1.25, "cache_read": 0.1}
RESET_WEEKDAY = 2  # Wednesday
RESET_HOUR = 11
DEFAULT_OTHER = "user@users-MacBook-Air.local"
LABEL = "com.trevskills.owa-usage"
USAGE_FIELDS = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_write": "cache_creation_input_tokens",
    "cache_read": "cache_read_input_tokens",
}
HEADER = ("| Week | This Mac | This Mac % | Other Mac | Other Mac % | 7d % "
          "| This Mac $ | Other Mac $ | Status |")


def home():
    return Path.home()


def report_dir():
    return home() / "Library/Mobile Documents/com~apple~CloudDocs/Claude Usage"


def parse_iso(s):
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t.astimezone()  # naive input is read as local time


def bounds_from_start(day):
    """Week starting on local date `day` at RESET_HOUR. Naive .astimezone() applies local DST."""
    start = dt.datetime(day.year, day.month, day.day, RESET_HOUR).astimezone()
    end_day = day + dt.timedelta(days=7)
    end = dt.datetime(end_day.year, end_day.month, end_day.day, RESET_HOUR).astimezone()
    return start, end


def week_bounds(now):
    local = now.astimezone()
    day = local.date() - dt.timedelta(days=(local.weekday() - RESET_WEEKDAY) % 7)
    start, end = bounds_from_start(day)
    if start > local:
        start, end = bounds_from_start(day - dt.timedelta(days=7))
    return start, end


def utc_key(t):
    # Transcript timestamps are UTC "YYYY-MM-DDTHH:MM:SS.mmmZ", so string order is time order.
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def count(since, until, owa_only):
    totals = {k: 0 for k in WEIGHTS}
    allowed = None
    if owa_only:
        env_dir = home() / ".claude-owa/session-env"
        allowed = {p.name for p in env_dir.iterdir() if p.is_dir()} if env_dir.is_dir() else set()
        if not allowed:
            return finish(totals)
    lo, hi = utc_key(since), utc_key(until)
    min_mtime = since.timestamp()
    seen = set()
    for root, _dirs, files in os.walk(str(home() / ".claude/projects")):
        for name in files:
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(root, name)
            try:
                if os.path.getmtime(path) < min_mtime:  # untouched since the window opened
                    continue
                fh = open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue
            with fh:
                for line in fh:
                    if '"usage"' not in line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    msg = rec.get("message")
                    if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                        continue
                    ts = rec.get("timestamp")
                    if not isinstance(ts, str) or not (lo <= ts < hi):
                        continue
                    if allowed is not None and rec.get("sessionId") not in allowed:
                        continue
                    key = (msg.get("id"), rec.get("requestId"))
                    if key in seen:
                        continue
                    seen.add(key)
                    for k, field in USAGE_FIELDS.items():
                        v = msg["usage"].get(field)
                        if isinstance(v, int):
                            totals[k] += v
    return finish(totals)


def finish(totals):
    totals["weighted"] = round(sum(totals[k] * w for k, w in WEIGHTS.items()))
    return totals


def other_host():
    return os.environ.get("OWA_USAGE_OTHER", DEFAULT_OTHER)


def other_mac(since, until):
    """The other Mac's count dict, or None when it is unreachable."""
    host = other_host()
    if host.startswith("-"):
        return None
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "--", host,
           "python3", "-", "count", "--since", since.isoformat(), "--until", until.isoformat()]
    try:
        with open(os.path.abspath(__file__), "rb") as src:
            res = subprocess.run(cmd, stdin=src, capture_output=True, timeout=300)
        data = json.loads(res.stdout.decode())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if res.returncode != 0 or not isinstance(data, dict) or not isinstance(data.get("weighted"), int):
        return None
    return data


def seven_day():
    """(used_percentage, resets_at, written_at) from usage.json, or None."""
    try:
        data = json.loads((home() / ".claude-owa/usage.json").read_text())
        sd = data["rate_limits"]["seven_day"]
        pct, resets, written = sd["used_percentage"], sd.get("resets_at"), data.get("written_at")
        if not isinstance(pct, (int, float)):
            return None
        return pct, resets, written
    except (OSError, ValueError, KeyError, TypeError):
        return None


def fmt_pct(x):
    return "{:.1f}%".format(x)


def cmd_week(now):
    start, end = week_bounds(now)
    mine = count(start, end, True)["weighted"]
    other = None
    if other_host():
        other = other_mac(start, end)
    theirs = other["weighted"] if other else 0
    total = mine + theirs
    sd = seven_day()
    print("OWA week {} -> {}".format(start.strftime("%a %Y-%m-%d %H:%M"), end.strftime("%a %Y-%m-%d %H:%M")))
    rows = [("this Mac ({})".format(socket.gethostname()), mine)]
    if other:
        rows.append(("other Mac ({})".format(other_host()), theirs))
    for label, w in rows:
        share = w / total if total else (1.0 if len(rows) == 1 else 0.0)
        pts = "{:.1f} pts".format(share * sd[0]) if sd else "- pts"
        print("{:<40} {:>16,} weighted  {:>6}  {:>9}  ${:.2f}".format(
            label, w, fmt_pct(share * 100), pts, PLAN_USD * share))
    if other_host() and other is None:
        print("other Mac unreachable")
    if sd and isinstance(sd[2], (int, float)):
        when = dt.datetime.fromtimestamp(sd[2]).strftime("%Y-%m-%d %H:%M")
        print("7d: {}% (as of {})".format(sd[0], when))
    else:
        print("7d: unknown")


def parse_rows(path):
    """Rows of a month file keyed by week start date string."""
    rows = {}
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 9:
            continue
        rows[cells[0].split()[0]] = {
            "mine": int(cells[1].replace(",", "")),
            "other": None if cells[3] == "-" else int(cells[3].replace(",", "")),
            "pct": cells[5],
            "status": cells[8],
        }
    return rows


def cents_split(values, total_cents):
    """Round shares of total_cents so they sum exactly (largest remainder)."""
    s = sum(values)
    if not s:
        return [0] * len(values)
    raw = [total_cents * v / s for v in values]
    out = [int(r) for r in raw]
    order = sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)
    for i in order[: total_cents - sum(out)]:
        out[i] += 1
    return out


def money(c):
    return "${}.{:02d}".format(c // 100, c % 100)


def render(month, rows):
    keys = sorted(rows)
    vals = []
    for k in keys:
        vals += [rows[k]["mine"], rows[k]["other"] or 0]
    cents = cents_split(vals, PLAN_USD * 100)
    month_total = sum(vals)
    mine_total = sum(vals[0::2])
    mine_c, other_c = sum(cents[0::2]), sum(cents[1::2])
    p = 100 * mine_total / month_total if month_total else 0
    q = 100 - p if month_total else 0
    out = ["# Claude Usage {}".format(month), "",
           "Total ${}: this Mac {} ({}), other Mac {} ({})".format(
               PLAN_USD, money(mine_c), fmt_pct(p), money(other_c), fmt_pct(q)),
           "", HEADER, "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for i, k in enumerate(keys):
        r = rows[k]
        week_total = r["mine"] + (r["other"] or 0)
        share = r["mine"] / week_total if week_total else 0
        end = dt.date.fromisoformat(k) + dt.timedelta(days=7)
        other = "-" if r["other"] is None else "{:,}".format(r["other"])
        other_share = "-" if r["other"] is None else fmt_pct(100 - 100 * share if week_total else 0)
        out.append("| {} -> {} | {:,} | {} | {} | {} | {} | {} | {} | {} |".format(
            k, end.isoformat(), r["mine"], fmt_pct(100 * share), other, other_share,
            r["pct"], money(cents[2 * i]), money(cents[2 * i + 1]), r["status"]))
    return "\n".join(out) + "\n"


def recount(start, end, now, old):
    mine = count(start, end, True)["weighted"]
    pending = False
    other = 0
    if other_host():
        got = other_mac(start, end)
        if got is None:
            pending = True
            other = old["other"] if old else None
        else:
            other = got["weighted"]
    pct = old["pct"] if old else "-"
    sd = seven_day()
    if sd and isinstance(sd[1], (int, float)) and abs(sd[1] - end.timestamp()) < 60:
        pct = "{}%".format(sd[0])
    status = "other Mac pending" if pending else ("in progress" if now < end else "final")
    return {"mine": mine, "other": other, "pct": pct, "status": status}


def cmd_report(now):
    out_dir = report_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    start, end = week_bounds(now)
    cur_month = end.strftime("%Y-%m")
    files = {p.stem: parse_rows(p) for p in out_dir.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].md")}
    files.setdefault(cur_month, {})
    cur_key = start.date().isoformat()
    files[cur_month].setdefault(cur_key, None)
    for month, rows in files.items():
        changed = False
        for key, old in list(rows.items()):
            if old is not None and old["status"] == "final":
                continue
            s, e = bounds_from_start(dt.date.fromisoformat(key))
            rows[key] = recount(s, e, now, old)
            changed = True
        if changed:
            (out_dir / (month + ".md")).write_text(render(month, rows))
    print("wrote {}".format(out_dir / (cur_month + ".md")))


def cmd_install():
    h = home()
    script = h / ".claude/skills/trevskills-owa-usage/owa_usage.py"
    plist = h / "Library/LaunchAgents" / (LABEL + ".plist")
    log = h / "Library/Logs/owa-usage.log"
    plist.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "Label": LABEL,
        "ProgramArguments": ["/usr/bin/python3", str(script), "report"],
        "StartInterval": 3600,
        "StartCalendarInterval": {"Weekday": 3, "Hour": 10, "Minute": 55},
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }
    with open(str(plist), "wb") as fh:
        plistlib.dump(data, fh)
    domain = "gui/{}".format(os.getuid())
    subprocess.run(["launchctl", "bootout", domain + "/" + LABEL], capture_output=True)
    res = subprocess.run(["launchctl", "bootstrap", domain, str(plist)], capture_output=True, text=True)
    if not script.exists():
        print("warning: {} is missing; sync the skill first".format(script))
    if res.returncode != 0:
        print("launchctl bootstrap failed: {}".format(res.stderr.strip()), file=sys.stderr)
        return 1
    print("installed {}".format(plist))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("count")
    c.add_argument("--since", required=True)
    c.add_argument("--until", required=True)
    c.add_argument("--owa-only", action="store_true")
    for name in ("week", "report"):
        sub.add_parser(name).add_argument("--now")
    sub.add_parser("install")
    a = ap.parse_args(argv)
    if a.cmd == "count":
        print(json.dumps(count(parse_iso(a.since), parse_iso(a.until), a.owa_only)))
        return 0
    if a.cmd == "install":
        return cmd_install()
    now = parse_iso(a.now) if a.now else dt.datetime.now().astimezone()
    if a.cmd == "week":
        cmd_week(now)
    else:
        cmd_report(now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
