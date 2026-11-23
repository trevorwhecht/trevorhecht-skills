"""Restart advice in `report`. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import os, subprocess, tempfile, unittest
from pathlib import Path

TOP = "Processes: 600 total\nPhysMem: 31G used\n\nPID    COMMAND          MEM\n4766   next-server (v15 23G\n"
# ps stub: `ps -o ppid=,comm= -p <pid>`; 4766's parent is launchd (orphan) unless `owned`.
PS = """#!/bin/sh
for a; do p="$a"; done
case "$p" in
  4766) echo "{ppid} next-server (v15.1.0)" ;;
  900) echo "  800 /bin/zsh" ;;
  800) echo "    1 /Applications/Ghostty.app/Contents/MacOS/ghostty" ;;
esac
"""

def report(up, swap_mb, owned=False):  # stub uptime, swap, top, ps; throwaway HOME because report writes ~/.mac-cleanup
    with tempfile.TemporaryDirectory() as tmp:
        stubs = {"uptime": f"#!/bin/sh\necho '13:38  up {up}, 6 users'\n",
                 "sysctl": f"#!/bin/sh\necho 'total = 24576.00M  used = {swap_mb}.00M'\n",
                 "top": f"#!/bin/sh\nprintf '{TOP}'\n",
                 "ps": PS.replace("{ppid}", "  900" if owned else "    1")}
        for name, body in stubs.items():
            Path(tmp, name).write_text(body); Path(tmp, name).chmod(0o755)
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

class MemoryHolder(unittest.TestCase):
    def test_orphan_named_and_stop_advised_before_restart(self):  # the 2026-11-22 case: 1 day up, 20 GB swap
        out = report("1 day,  4:36", 20000)
        self.assertIn("Biggest memory holder: next-server (v15.1.0) (pid 4766) at 23G", out)
        self.assertIn("ORPHAN", out)
        self.assertLess(out.index("STOP IT FIRST: kill 4766"), out.index("RESTART RECOMMENDED"))
        self.assertLess(out.index("STOP FIRST: next-server (v15.1.0) (pid 4766, 23G, orphan)"),
                        out.index("RESTART NOW-ISH"))

    def test_owned_holder_names_its_app(self):
        out = report("1 day,  4:36", 20000, owned=True)
        self.assertIn("Biggest memory holder: next-server (v15.1.0) (pid 4766) at 23G", out)
        self.assertNotIn("ORPHAN", out)
        self.assertIn("Started under ghostty", out)
        self.assertIn("STOP FIRST: next-server (v15.1.0) (pid 4766, 23G, started under ghostty)", out)

    def test_no_holder_line_when_swap_low(self):
        out = report("8 days,  4:36", 100)
        self.assertNotIn("Biggest memory holder", out)
        self.assertNotIn("STOP FIRST", out)

if __name__ == "__main__":
    unittest.main()
