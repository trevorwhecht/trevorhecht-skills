"""Tests for owa_usage.py. Run: python3 -m unittest discover -s macos/skills/trevskills-owa-usage -p 'test_*.py'"""
import datetime as dt
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "owa_usage.py"
PY = "/usr/bin/python3" if os.path.exists("/usr/bin/python3") else sys.executable  # 3.9 on macOS
TZ = "America/Los_Angeles"
OWA_SID = "11111111-aaaa-bbbb-cccc-000000000001"
OTHER_SID = "22222222-aaaa-bbbb-cccc-000000000002"

sys.path.insert(0, str(HERE))
import owa_usage  # noqa: E402


def setUpModule():
    os.environ["TZ"] = TZ
    time.tzset()


def rec(sid, mid, rid, ts, i=0, o=0, cw=0, cr=0):
    return json.dumps({
        "type": "assistant", "sessionId": sid, "requestId": rid, "timestamp": ts,
        "message": {"id": mid, "usage": {
            "input_tokens": i, "output_tokens": o,
            "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr}},
    }) + "\n"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.other = self.tmp / "other"
        self.bin = self.tmp / "bin"
        for p in (self.home, self.other, self.bin):
            p.mkdir()
        (self.home / ".claude-owa/session-env" / OWA_SID).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(str(self.tmp))

    def write(self, home, rel, *lines):
        p = home / ".claude/projects/proj" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(str(p), "a") as fh:
            fh.write("".join(lines))

    def usage(self, pct, resets, written=1794893924):
        (self.home / ".claude-owa/usage.json").write_text(json.dumps(
            {"rate_limits": {"seven_day": {"used_percentage": pct, "resets_at": resets}}, "written_at": written}))

    def fake_ssh(self, reachable):
        body = ("#!/bin/sh\nexit 255\n" if not reachable else
                "#!{py}\nimport os, subprocess, sys\na = sys.argv[1:]\ni = a.index('python3')\n"
                "env = dict(os.environ, HOME={home!r})\n"
                "sys.exit(subprocess.call([{py!r}] + a[i + 1:], env=env))\n").format(py=PY, home=str(self.other))
        p = self.bin / "ssh"
        p.write_text(body)
        p.chmod(0o755)

    def run_cli(self, *args, other="fake@host"):
        env = dict(os.environ, HOME=str(self.home), TZ=TZ, OWA_USAGE_OTHER=other,
                   PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        return subprocess.run([PY, str(SCRIPT)] + list(args), env=env, capture_output=True, text=True)

    def month_file(self, month):
        return self.home / "Library/Mobile Documents/com~apple~CloudDocs/Claude Usage" / (month + ".md")


class TestCount(Base):
    def test_weights_dedup_window(self):
        a = rec(OWA_SID, "msg_a", "req_a", "2026-11-12T10:00:00.000Z", 100, 10, 1000, 10000)
        self.write(self.home, OWA_SID + ".jsonl",
                   a, a,  # same message written twice (one line per content block)
                   rec(OWA_SID, "msg_d", "req_d", "2026-11-11T19:00:00.000Z", 1, 1, 4, 10),  # == since
                   rec(OWA_SID, "msg_b", "req_b", "2026-11-11T18:59:59.999Z", 7, 7, 7, 7),  # before since
                   rec(OWA_SID, "msg_c", "req_c", "2026-11-18T19:00:00.000Z", 9, 9, 9, 9))  # == until
        self.write(self.home, "resumed.jsonl", a)  # resumed transcript repeats the parent's record
        r = self.run_cli("count", "--since", "2026-11-11T11:00:00-08:00", "--until", "2026-11-18T11:00:00-08:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), {
            "input": 101, "output": 11, "cache_write": 1004, "cache_read": 10010,
            "weighted": 2412})  # 100+50+1250+1000 + 1+5+5+1

    def test_owa_only_filter(self):
        self.write(self.home, OWA_SID + ".jsonl", rec(OWA_SID, "m1", "r1", "2026-11-12T10:00:00Z", 100))
        self.write(self.home, OWA_SID + "/subagents/agent-x.jsonl", rec(OWA_SID, "m2", "r2", "2026-11-12T10:00:00Z", 20))
        self.write(self.home, OTHER_SID + ".jsonl", rec(OTHER_SID, "m3", "r3", "2026-11-12T10:00:00Z", 3000))
        args = ("count", "--since", "2026-11-11T11:00:00-08:00", "--until", "2026-11-18T11:00:00-08:00")
        r = self.run_cli(*args, "--owa-only")
        self.assertEqual(json.loads(r.stdout)["weighted"], 120)
        self.assertEqual(json.loads(self.run_cli(*args).stdout)["weighted"], 3120)
        shutil.rmtree(str(self.home / ".claude-owa/session-env"))
        r = self.run_cli(*args, "--owa-only")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["weighted"], 0)


class TestWeeks(unittest.TestCase):
    def local(self, s):
        return dt.datetime.fromisoformat(s).astimezone()

    def test_week_bounds_and_month(self):
        cases = [
            ("2026-11-11 10:59", "2026-11-04 11:00"),  # Wednesday before reset
            ("2026-11-11 11:00", "2026-11-11 11:00"),  # Wednesday at reset
            ("2026-11-17 23:00", "2026-11-11 11:00"),  # Tuesday night
        ]
        for now, want in cases:
            start, end = owa_usage.week_bounds(self.local(now))
            self.assertEqual(start.strftime("%Y-%m-%d %H:%M"), want, now)
            self.assertEqual(end - start, dt.timedelta(days=7), now)
            self.assertEqual(end.strftime("%a %H:%M"), "Wed 11:00", now)
        start, end = owa_usage.week_bounds(self.local("2026-10-30 09:00"))
        self.assertEqual(start.strftime("%Y-%m-%d %H:%M"), "2026-10-28 11:00")
        self.assertEqual(end.strftime("%Y-%m-%d %H:%M %z"), "2026-11-04 11:00 -0800")  # PST after DST ends
        self.assertEqual(start.strftime("%z"), "-0700")
        self.assertEqual(end.strftime("%Y-%m"), "2026-11")


class TestWeek(Base):
    def seed(self):
        self.write(self.home, OWA_SID + ".jsonl", rec(OWA_SID, "m1", "r1", "2026-11-12T00:00:00Z", 100, 10, 1000, 10000))
        self.write(self.other, "x.jsonl", rec("any", "m2", "r2", "2026-11-13T00:00:00Z", 600))

    def test_both_macs_and_unreachable(self):
        self.seed()
        self.usage(40, 1795028400)
        self.fake_ssh(True)
        r = self.run_cli("week", "--now", "2026-11-16T12:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        mine = [l for l in lines if l.startswith("this Mac")]
        other = [l for l in lines if l.startswith("other Mac (fake@host)")]
        self.assertEqual(len(mine), 1, r.stdout)
        self.assertEqual(len(other), 1, r.stdout)
        for want in ("2,400 weighted", "80.0%", "32.0 pts", "$160.00"):
            self.assertIn(want, mine[0])
        for want in ("600 weighted", "20.0%", "8.0 pts", "$40.00"):
            self.assertIn(want, other[0])
        self.assertEqual(lines[-1], "7d: 40% (as of 2026-11-16 21:38)")
        self.assertNotIn("unreachable", r.stdout)

        self.fake_ssh(False)
        (self.home / ".claude-owa/usage.json").write_text("{not json")
        r = self.run_cli("week", "--now", "2026-11-16T12:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        mine = [l for l in lines if l.startswith("this Mac")]
        self.assertIn("100.0%", mine[0])
        self.assertIn("$200.00", mine[0])
        self.assertFalse([l for l in lines if l.startswith("other Mac (")], r.stdout)
        self.assertIn("other Mac unreachable", lines)
        self.assertEqual(lines[-1], "7d: unknown")

        (self.home / ".claude-owa/usage.json").unlink()
        self.assertEqual(self.run_cli("week", "--now", "2026-11-16T12:00").stdout.splitlines()[-1], "7d: unknown")


W1_END = 1793818800  # 2026-11-04 11:00 PST
W2_END = 1794423600  # 2026-11-11 11:00 PST


class TestReport(Base):
    def seed(self):
        self.write(self.home, OWA_SID + ".jsonl",
                   rec(OWA_SID, "a1", "r", "2026-10-29T00:00:00Z", 300),
                   rec(OWA_SID, "a2", "r", "2026-11-05T00:00:00Z", 100))
        self.write(self.other, "x.jsonl",
                   rec("s", "b1", "r", "2026-10-30T00:00:00Z", 100),
                   rec("s", "b2", "r", "2026-11-06T00:00:00Z", 500))

    def test_row_and_totals(self):
        self.seed()
        self.fake_ssh(True)
        self.usage(90, W1_END)
        self.assertEqual(self.run_cli("report", "--now", "2026-11-03T12:00").returncode, 0)
        self.usage(55, W2_END)
        r = self.run_cli("report", "--now", "2026-11-10T12:00")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.month_file("2026-11").read_text()
        lines = text.splitlines()
        self.assertIn("Total $200: this Mac $80.00 (40.0%), other Mac $120.00 (60.0%)", lines[:3])
        rows = [l for l in lines if l.startswith("| 20")]
        self.assertEqual(rows, [
            "| 2026-10-28 -> 2026-11-04 | 300 | 75.0% | 100 | 25.0% | 90% | $60.00 | $20.00 | final |",
            "| 2026-11-04 -> 2026-11-11 | 100 | 16.7% | 500 | 83.3% | 55% | $20.00 | $100.00 | in progress |",
        ])
        dollars = [float(c.strip()[1:]) for l in rows for c in l.split("|")[7:9]]
        self.assertAlmostEqual(sum(dollars), 200.0, delta=0.01)

    def test_cents_sum_with_thirds(self):
        self.assertEqual(sum(owa_usage.cents_split([1, 1, 1, 1, 1, 1, 1], 20000)), 20000)
        self.assertEqual(owa_usage.cents_split([1, 1, 1], 20000), [6667, 6667, 6666])

    def test_rerun_no_duplicate_and_backfill(self):
        self.seed()
        self.fake_ssh(False)
        self.assertEqual(self.run_cli("report", "--now", "2026-11-10T12:00").returncode, 0)
        f = self.month_file("2026-11")
        first = f.read_text()
        self.assertIn("| 2026-11-04 -> 2026-11-11 | 100 | 100.0% | - | - | - | $200.00 | $0.00 | other Mac pending |", first)
        self.run_cli("report", "--now", "2026-11-10T12:00")
        self.assertEqual(f.read_text(), first)
        self.assertEqual(first.count("| 2026-11-04 "), 1)

        self.fake_ssh(True)
        self.run_cli("report", "--now", "2026-11-12T12:00")
        rows = [l for l in f.read_text().splitlines() if l.startswith("| 20")]
        self.assertEqual(rows[0], "| 2026-11-04 -> 2026-11-11 | 100 | 16.7% | 500 | 83.3% | - | $33.33 | $166.67 | final |")
        self.assertTrue(rows[1].startswith("| 2026-11-11 -> 2026-11-18 | 0 |"), rows[1])
        self.assertTrue(rows[1].endswith("| in progress |"), rows[1])

        # A final row is never recounted, even when new records land in its window.
        self.write(self.home, OWA_SID + ".jsonl", rec(OWA_SID, "late", "r", "2026-11-07T00:00:00Z", 9999))
        self.run_cli("report", "--now", "2026-11-12T12:00")
        self.assertEqual([l for l in f.read_text().splitlines() if l.startswith("| 2026-11-04")], rows[:1])


class TestInstall(Base):
    def test_plist(self):
        log = self.tmp / "launchctl.log"
        p = self.bin / "launchctl"
        p.write_text("#!/bin/sh\necho \"$@\" >> '{}'\n".format(log))
        p.chmod(0o755)
        r = self.run_cli("install")
        self.assertEqual(r.returncode, 0, r.stderr)
        plist = self.home / "Library/LaunchAgents/com.trevskills.owa-usage.plist"
        self.assertEqual(subprocess.run(["plutil", "-lint", str(plist)], capture_output=True).returncode, 0)
        with open(str(plist), "rb") as fh:
            data = plistlib.load(fh)
        args = data["ProgramArguments"]
        self.assertEqual(args[-1], "report")
        self.assertEqual(args[1], str(self.home) + "/.claude/skills/trevskills-owa-usage/owa_usage.py")
        for path in args[:2] + [data["StandardOutPath"], data["StandardErrorPath"]]:
            self.assertTrue(path.startswith("/"), path)
            self.assertNotIn(str(HERE), path)
        self.assertTrue(data["StandardOutPath"].startswith(str(self.home) + "/"))
        self.assertEqual(data["StartInterval"], 3600)
        self.assertEqual(data["StartCalendarInterval"], {"Weekday": 3, "Hour": 10, "Minute": 55})
        self.assertIn("bootstrap gui/{} {}".format(os.getuid(), plist), log.read_text())


if __name__ == "__main__":
    unittest.main()
