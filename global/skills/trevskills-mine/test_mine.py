"""Tests for mine.py on a temp HOME, with a fake rclone on PATH.

run: python3 -m unittest discover -s global/skills/trevskills-mine -p 'test_*.py'
"""
import json, lzma, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "mine.py"
DAY = 86400

# Fake rclone. FAKE_DRIVE is the drive root ("gdrive:x/y" -> FAKE_DRIVE/x/y); FAKE_MODE picks behaviour.
FAKE_RCLONE = f"""#!{sys.executable}
import hashlib, json, os, shutil, sys
from pathlib import Path
mode, drive = os.environ.get("FAKE_MODE", "ok"), Path(os.environ["FAKE_DRIVE"])
if mode == "fail-if-called":
    open(os.environ["FAKE_CALLED"], "w").write(" ".join(sys.argv))
    sys.exit(3)
args = [a for a in sys.argv[1:] if a != "--"]
loc = lambda r: drive / r.partition(":")[2]
if args[0] == "listremotes":
    print(os.environ.get("FAKE_REMOTES", "gdrive:"))
elif args[0] == "copyto":
    if mode == "copy-fails":
        print("ERROR: upload refused", file=sys.stderr)
        sys.exit(1)
    dst = loc(args[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args[1], dst)
elif args[0] == "lsjson":
    p = loc(args[-1])
    if not p.is_file():
        print("[]")
        sys.exit(0)
    data = p.read_bytes()
    size = len(data) + (1 if mode == "wrong-size" else 0)
    print(json.dumps([{{"Path": p.name, "Name": p.name, "Size": size,
                        "Hashes": {{"md5": hashlib.md5(data).hexdigest()}}}}]))
else:
    sys.exit(2)
"""


def rec(role, text, **extra):
    return {"type": role, "timestamp": "2026-09-01T00:00:00Z", "cwd": "/work/proj",
            "message": {"role": role, "content": text}, **extra}


class MineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.home, self.drive, self.bin = base / "home", base / "drive", base / "bin"
        self.root = self.home / ".claude" / "projects"
        self.marker = self.home / ".claude" / "transcript-mining" / "last-mined"
        for d in (self.root, self.drive, self.bin):
            d.mkdir(parents=True)
        fake = self.bin / "rclone"
        fake.write_text(FAKE_RCLONE)
        fake.chmod(0o755)
        self.called = base / "rclone-called"
        self.now = time.time()

    def session(self, rel, age_days, entry=None, body="please fix the parser"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        extra = {"entrypoint": entry} if entry else {}
        lines = [rec("user", body, **extra), rec("assistant", "done, parser fixed")] * 40
        p.write_text("".join(json.dumps(l) + "\n" for l in lines))
        t = self.now - age_days * DAY
        os.utime(p, (t, t))
        return p

    def set_marker(self, epoch):
        self.marker.parent.mkdir(parents=True, exist_ok=True)
        self.marker.write_text(f"{int(epoch)}\n")

    def run_mine(self, *args, mode="ok", rclone=True, remotes="gdrive:"):
        env = {"HOME": str(self.home), "PATH": str(self.bin) if rclone else str(self.drive),
               "FAKE_DRIVE": str(self.drive), "FAKE_MODE": mode, "FAKE_REMOTES": remotes,
               "FAKE_CALLED": str(self.called)}
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)

    def snapshot(self):
        return sorted((str(p), p.stat().st_mtime) for p in Path(self.tmp.name).rglob("*")
                      if p.is_file() and p != self.called)

    def test_archive_selects_only_mined_old_interactive(self):
        picked = self.session("-work-proj/aaaa.jsonl", 40)
        self.session("-work-proj/bbbb.jsonl", 35)  # newer than the marker
        self.session("-work-proj/cccc.jsonl", 5)
        self.session("-work-proj/dddd.jsonl", 40, entry="sdk-cli")
        self.session("-work-proj/aaaa/subagents/agent-1.jsonl", 40)
        self.set_marker(self.now - 38 * DAY)
        r = self.run_mine("archive", mode="fail-if-called")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], f"would archive {picked} -> gdrive:claude-transcripts/-work-proj/aaaa.jsonl.xz")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1], f"mine: 1 to archive, {picked.stat().st_size} bytes (dry run)")

    def test_archive_subagents_of_archived_session(self):
        orphan = self.session("-work-proj/gone/subagents/agent-1.jsonl", 40)
        self.session("-work-proj/kept.jsonl", 40)
        self.session("-work-proj/kept/subagents/agent-2.jsonl", 40)
        self.session("-work-proj/gone/subagents/agent-3.jsonl", 5)
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        remote = self.drive / "claude-transcripts" / "-work-proj" / "gone" / "subagents" / "agent-1.jsonl.xz"
        self.assertTrue(remote.exists())
        self.assertFalse(orphan.exists())
        self.assertTrue((self.root / "-work-proj/kept/subagents/agent-2.jsonl").exists())
        self.assertTrue((self.root / "-work-proj/gone/subagents/agent-3.jsonl").exists())

    def test_archive_no_marker(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        r = self.run_mine("archive", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mine: no last-mined marker, nothing to archive", r.stdout)
        self.assertTrue(p.exists())
        self.assertEqual(list(self.drive.iterdir()), [])

    def test_archive_dry_run_touches_nothing(self):
        a = self.session("-work-proj/aaaa.jsonl", 40)
        b = self.session("-other/eeee.jsonl", 50)
        self.set_marker(self.now)
        before = self.snapshot()
        r = self.run_mine("archive", "--remote", "gdrive:x", mode="fail-if-called")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.called.exists())
        self.assertIn(f"would archive {a} -> gdrive:x/-work-proj/aaaa.jsonl.xz", r.stdout)
        self.assertIn(f"would archive {b} -> gdrive:x/-other/eeee.jsonl.xz", r.stdout)
        self.assertEqual(r.stdout.splitlines()[-1],
                         f"mine: 2 to archive, {a.stat().st_size + b.stat().st_size} bytes (dry run)")

    def test_archive_dry_run_nothing(self):
        self.session("-work-proj/cccc.jsonl", 5)
        self.set_marker(self.now)
        r = self.run_mine("archive", mode="fail-if-called")
        self.assertEqual((r.returncode, r.stdout), (0, "mine: nothing to archive\n"))

    def test_archive_apply_without_rclone(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply", rclone=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("mine: rclone not found, nothing archived", r.stderr)
        self.assertTrue(p.exists())

    def test_archive_apply_remote_missing(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply", remotes="gdrive2:\nother:")
        self.assertEqual(r.returncode, 1)
        self.assertIn("mine: rclone remote gdrive: not configured, nothing archived", r.stderr)
        self.assertTrue(p.exists())
        self.assertEqual(list(self.drive.iterdir()), [])

    def test_archive_apply_uploads_verifies_deletes(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        original = p.read_bytes()
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"archived {p}", r.stdout)
        remote = self.drive / "claude-transcripts" / "-work-proj" / "aaaa.jsonl.xz"
        self.assertEqual(lzma.decompress(remote.read_bytes()), original)
        self.assertFalse(p.exists())

    def test_archive_apply_keeps_on_size_mismatch(self):
        a = self.session("-work-proj/aaaa.jsonl", 40)
        b = self.session("-work-proj/ffff.jsonl", 45)
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply", mode="wrong-size")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"kept {a}: ", r.stdout)
        self.assertIn(f"kept {b}: ", r.stdout)  # went on to the next session
        self.assertTrue(a.exists())
        self.assertTrue(b.exists())

    def test_archive_apply_keeps_on_upload_failure(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        self.set_marker(self.now)
        r = self.run_mine("archive", "--apply", mode="copy-fails")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"kept {p}: ", r.stdout)
        self.assertIn("upload refused", r.stdout)
        self.assertTrue(p.exists())

    def test_archive_apply_rerun_after_partial(self):
        p = self.session("-work-proj/aaaa.jsonl", 40)
        original = p.read_bytes()
        stale = self.drive / "claude-transcripts" / "-work-proj" / "aaaa.jsonl.xz"
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"stale partial upload")
        self.set_marker(self.now)
        tmp_before = set(Path(tempfile.gettempdir()).glob("mine-archive-*"))
        r = self.run_mine("archive", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"archived {p}", r.stdout)
        self.assertEqual(lzma.decompress(stale.read_bytes()), original)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("mine-archive-*")), tmp_before)

    def test_rank_and_mark_unchanged(self):
        p = self.session("-work-proj/aaaa.jsonl", 1)
        r = self.run_mine("candidates")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith(f"{p}\t"), r.stdout)
        self.assertIn("please fix the parser", r.stdout)
        r = self.run_mine("mark", "1700000000.7")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.marker.read_text(), "1700000000\n")


if __name__ == "__main__":
    unittest.main()
