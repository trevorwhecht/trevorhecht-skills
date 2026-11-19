"""Restart advice in `report`. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import os, subprocess, tempfile, unittest
from pathlib import Path

def report(up, swap_mb):  # stub uptime + swap; throwaway HOME because report writes ~/.mac-cleanup
    with tempfile.TemporaryDirectory() as tmp:
        for name, out in (("uptime", f"13:38  up {up}, 6 users"), ("sysctl", f"total = 6144.00M  used = {swap_mb}.00M")):
            Path(tmp, name).write_text(f"#!/bin/sh\necho '{out}'\n"); Path(tmp, name).chmod(0o755)
        env = dict(os.environ, HOME=tmp, PATH=f"{tmp}:{os.environ['PATH']}")
        return subprocess.run(["bash", str(Path(__file__).with_name("trevskills-mac-cleanup.sh")), "report"],
                              env=env, capture_output=True, text=True).stdout

class RestartBanner(unittest.TestCase):
    def test_restart_advice(self):  # (uptime, swap MB, restart banner + plan line, "will not help" note)
        for up, swap, restart, note in (("4:36", 3300, False, True), ("2 days,  4:36", 3300, True, False),
                                        ("8 days,  4:36", 100, True, False), ("4:36", 100, False, False)):
            out = report(up, swap)
            got = ("RESTART RECOMMENDED" in out, "RESTART NOW-ISH" in out, "a restart will not help" in out)
            self.assertEqual(got, (restart, restart, note), f"up {up}, swap {swap} MB")
