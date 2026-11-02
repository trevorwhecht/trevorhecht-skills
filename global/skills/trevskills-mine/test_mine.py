"""Tests for mine.py archive on a temp projects tree.

run: python3 -m unittest discover -s global/skills/trevskills-mine -p 'test_*.py'
"""
import contextlib, io, lzma, os, sys, tempfile, time, unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mine  # noqa: E402

DAY = 86400


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root, self.dest = base / "projects", base / "drive" / "claude-transcript-archive"
        self.marker, self.cloud = base / "last-mined", base / "cloud"
        self.root.mkdir()
        self.cloud.mkdir()
        for name, val in (("ROOT", self.root), ("MARKER", self.marker), ("CLOUD", self.cloud)):
            p = mock.patch.object(mine, name, val)
            p.start()
            self.addCleanup(p.stop)
        self.now = time.time()

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, age_days, body=None):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if body is not None else f'{{"rel": "{rel}"}}\n'.encode() * 50)
        t = self.now - age_days * DAY
        os.utime(p, (t, t))
        return p

    def set_marker(self, epoch):
        self.marker.write_text(f"{int(epoch)}\n")

    def run_archive(self, apply=True, dest="default"):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = mine.archive(self.dest if dest == "default" else dest, days=30, apply=apply)
        return rc, out.getvalue()

    def files_under_dest(self):
        return sorted(str(p.relative_to(self.dest)) for p in self.dest.rglob("*") if p.is_file()) \
            if self.dest.exists() else []

    def test_archive_apply_moves_old_mined_files(self):
        a = self.put("p/a.jsonl", 40)
        b = self.put("p/sub/subagents/b.jsonl", 40)
        new = self.put("p/new.jsonl", 5)
        m = self.put("p/memory/m.jsonl", 40)
        a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
        self.set_marker(self.now)
        rc, _ = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertEqual(self.files_under_dest(), ["p/a.jsonl.xz", "p/sub/subagents/b.jsonl.xz"])
        self.assertEqual(lzma.decompress((self.dest / "p/a.jsonl.xz").read_bytes()), a_bytes)
        self.assertEqual(lzma.decompress((self.dest / "p/sub/subagents/b.jsonl.xz").read_bytes()), b_bytes)
        self.assertFalse(a.exists())
        self.assertFalse(b.exists())
        self.assertTrue(new.exists())
        self.assertTrue(m.exists())

    def test_archive_skips_unmined(self):
        p = self.put("p/a.jsonl", 40)
        self.set_marker(self.now - 50 * DAY)
        rc, _ = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertTrue(p.exists())
        self.assertEqual(self.files_under_dest(), [])

    def test_archive_no_marker(self):
        p = self.put("p/a.jsonl", 40)
        rc, out = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertIn("mine: no last-mined marker, archive skipped", out)
        self.assertTrue(p.exists())
        self.assertFalse(self.dest.exists())

    def test_archive_dry_run_changes_nothing(self):
        a = self.put("p/a.jsonl", 40, b"x" * 1234)
        b = self.put("p/b.jsonl", 40, b"y" * 99)
        self.set_marker(self.now)
        rc, out = self.run_archive(apply=False)
        self.assertEqual(rc, 0)
        self.assertIn(f"1234\t{a}", out)
        self.assertIn(f"99\t{b}", out)
        self.assertIn("2 file(s)", out)
        self.assertTrue(a.exists())
        self.assertTrue(b.exists())
        self.assertFalse(self.dest.exists())

    def test_archive_verify_failure_keeps_original(self):
        a = self.put("p/a.jsonl", 40)
        self.set_marker(self.now)
        with mock.patch.object(mine, "same_xz", return_value=False):
            rc, out = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertTrue(a.exists())
        self.assertIn("KEPT (verify failed)", out)
        self.assertEqual(self.files_under_dest(), [])

    def test_archive_oserror_keeps_original(self):
        a = self.put("p/a.jsonl", 40)
        self.set_marker(self.now)
        with mock.patch.object(mine.lzma, "open", side_effect=OSError("disk full")):
            rc, out = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertTrue(a.exists())
        self.assertIn("KEPT (disk full)", out)
        self.assertEqual(self.files_under_dest(), [])

    def test_archive_existing_target_kept(self):
        a = self.put("p/a.jsonl", 40)
        target = self.dest / "p" / "a.jsonl.xz"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"old archive")
        self.set_marker(self.now)
        rc, out = self.run_archive()
        self.assertEqual(rc, 0)
        self.assertTrue(a.exists())
        self.assertIn("KEPT (archive exists)", out)
        self.assertEqual(target.read_bytes(), b"old archive")

    def test_archive_no_drive_folder(self):
        a = self.put("p/a.jsonl", 40)
        self.set_marker(self.now)
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["mine.py", "archive", "--apply"]), contextlib.redirect_stdout(out):
            rc = mine.main()
        self.assertEqual(rc, 0)
        self.assertIn("mine: no Google Drive folder, archive skipped", out.getvalue())
        self.assertTrue(a.exists())
        self.assertEqual(list(self.cloud.iterdir()), [])

    def test_drive_dest_picks_first_sorted(self):
        (self.cloud / "GoogleDrive-b" / "My Drive").mkdir(parents=True)
        (self.cloud / "GoogleDrive-a" / "My Drive").mkdir(parents=True)
        self.assertEqual(mine.drive_dest(), self.cloud / "GoogleDrive-a" / "My Drive" / "claude-transcript-archive")


if __name__ == "__main__":
    unittest.main()
