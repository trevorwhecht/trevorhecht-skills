"""Restart advice in `report`. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import os, subprocess, tempfile, unittest
from pathlib import Path

TOP = "Processes: 600 total\nPhysMem: 31G used\n\nPID    COMMAND          MEM\n4766   next-server (v15 23G\n"
# ps stub: `ps -o ppid=,comm= -p <pid>` and `ps -o etime= -p <pid>`. 4766's parent is launchd (orphan),
# ghostty's zsh (900) or a claude CLI (700) whose parent is launchd; 4766 is 2 days old unless `etime` says otherwise.
PS = """#!/bin/sh
for a; do p="$a"; done
if [ "$2" = "etime=" ]; then [ "$p" = 4766 ] && printf '%s\\n' '{etime}'; exit 0; fi
case "$p" in
  4766) echo "{ppid} next-server (v15.1.0)" ;;
  900) echo "  800 /bin/zsh" ;;
  800) echo "    1 /Applications/Ghostty.app/Contents/MacOS/ghostty" ;;
  700) echo "    1 /Users/x/.local/bin/claude" ;;
esac
"""
# lsof stub: `lsof -a -d cwd -p <pid> -Fn` prints the cwd as an `n` line, or nothing when `cwd` is empty.
LSOF = """#!/bin/sh
[ -n '{cwd}' ] && printf 'p4766\\nfcwd\\nn%s\\n' '{cwd}'
exit 0
"""
PARENT = {"launchd": "    1", "ghostty": "  900", "claude": "  700"}

def report(up, swap_mb, owned=False, chain="launchd", etime="2-03:04:05", cwd="/Users/x/repo", code=False):  # stub uptime, swap, top, ps; throwaway HOME because report writes ~/.mac-cleanup
    with tempfile.TemporaryDirectory() as tmp:
        stubs = {"uptime": f"#!/bin/sh\necho '13:38  up {up}, 6 users'\n",
                 "sysctl": f"#!/bin/sh\necho 'total = 24576.00M  used = {swap_mb}.00M'\n",
                 "top": f"#!/bin/sh\nprintf '{TOP}'\n",
                 "ps": PS.replace("{ppid}", PARENT["ghostty" if owned else chain]).replace("{etime}", etime),
                 "lsof": LSOF.replace("{cwd}", cwd)}
        for name, body in stubs.items():
            Path(tmp, name).write_text(body); Path(tmp, name).chmod(0o755)
        env = dict(os.environ, HOME=tmp, PATH=f"{tmp}:{os.environ['PATH']}")
        run = subprocess.run(["bash", str(Path(__file__).with_name("trevskills-mac-cleanup.sh")), "report"],
                             env=env, capture_output=True, text=True)
        return (run.stdout, run.returncode) if code else run.stdout

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

    def assert_live(self, out, reason):
        self.assertIn("Biggest memory holder: next-server (v15.1.0) (pid 4766) at 23G", out)
        self.assertIn(f"  It is live work ({reason}): let it finish; not a stop target.", out)
        for word in ("ORPHAN", "Started under", "STOP IT FIRST", "STOP FIRST:"):
            self.assertNotIn(word, out)

    def test_holder_under_claude_is_not_a_stop_target(self):
        out = report("1 day,  4:36", 20000, chain="claude")
        self.assert_live(out, "under claude")
        self.assertIn("RESTART RECOMMENDED", out)
        self.assertIn("RESTART NOW-ISH", out)

    def test_holder_in_scrum_worktree_is_not_a_stop_target(self):
        out = report("1 day,  4:36", 20000, cwd="/Users/x/repo/.claude/worktrees/scrum-1979-foo/app")
        self.assert_live(out, "scrum worktree")

    def test_young_holder_is_not_a_stop_target(self):
        self.assert_live(report("1 day,  4:36", 20000, etime="00:07"), "started 7s ago")
        self.assert_live(report("1 day,  4:36", 20000, etime="09:59"), "started 599s ago")
        out = report("1 day,  4:36", 20000, etime="10:00")
        self.assertIn("ORPHAN", out)
        self.assertIn("STOP FIRST: next-server (v15.1.0) (pid 4766, 23G, orphan)", out)
        self.assertNotIn("live work", out)

    def test_missing_cwd_and_bad_etime_fall_back_to_orphan(self):
        for etime in ("", "garbage", "1:xx"):
            out, rc = report("1 day,  4:36", 20000, etime=etime, cwd="", code=True)
            self.assertEqual(rc, 0, f"etime {etime!r}")
            self.assertIn("ORPHAN", out, f"etime {etime!r}")
            self.assertIn("STOP IT FIRST: kill 4766", out, f"etime {etime!r}")
            self.assertNotIn("live work", out, f"etime {etime!r}")

if __name__ == "__main__":
    unittest.main()
