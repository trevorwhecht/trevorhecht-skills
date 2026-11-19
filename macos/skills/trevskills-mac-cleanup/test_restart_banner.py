"""Restart advice in `report`. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "trevskills-mac-cleanup.sh"
UPTIME = {0: "13:38  up  4:36, 6 users, load averages: 9.1 8.2 7.0",
          2: "13:38  up 2 days,  4:36, 6 users, load averages: 1.1 1.2 1.0",
          8: "13:38  up 8 days,  4:36, 6 users, load averages: 1.1 1.2 1.0"}


def report(days, swap_mb):
    """Run `report` with stubbed uptime/swap and a throwaway HOME (report writes ~/.mac-cleanup)."""
    with tempfile.TemporaryDirectory() as tmp:
        stubs = Path(tmp, "bin"); stubs.mkdir()
        for name, out in (("uptime", UPTIME[days]),
                          ("sysctl", f"total = 6144.00M  used = {swap_mb}.00M  free = 100.00M  (encrypted)")):
            stub = stubs / name
            stub.write_text(f"#!/bin/sh\necho '{out}'\n"); stub.chmod(0o755)
        env = dict(os.environ, HOME=tmp, PATH=f"{stubs}:{os.environ['PATH']}")
        return subprocess.run(["bash", str(SCRIPT), "report"], env=env, capture_output=True, text=True).stdout


class RestartBanner(unittest.TestCase):
    def test_heavy_swap_right_after_restart_says_restart_wont_help(self):
        out = report(0, 3300)
        self.assertNotIn("RESTART RECOMMENDED", out)
        self.assertNotIn("RESTART NOW-ISH", out)
        self.assertIn("a restart will not help", out)

    def test_heavy_swap_after_a_day_recommends_restart(self):
        out = report(2, 3300)
        self.assertIn("RESTART RECOMMENDED", out)
        self.assertIn("RESTART NOW-ISH", out)

    def test_week_of_uptime_recommends_restart(self):
        out = report(8, 100)
        self.assertIn("RESTART RECOMMENDED", out)
        self.assertIn("RESTART NOW-ISH", out)

    def test_fresh_and_light_says_nothing(self):
        out = report(0, 100)
        self.assertNotIn("RESTART RECOMMENDED", out)
        self.assertNotIn("a restart will not help", out)


if __name__ == "__main__":
    unittest.main()
