"""Shop Mac mode. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import os, subprocess, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("trevskills-mac-cleanup.sh")


def clean(claude_md, pgrep_exit, *cats):
    """Dry-run `clean` in a temp HOME, with a fake pgrep deciding whether npm is in use."""
    with tempfile.TemporaryDirectory() as t:
        home, bin_ = Path(t) / "home", Path(t) / "bin"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "CLAUDE.md").write_text(claude_md)
        bin_.mkdir()
        fake = bin_ / "pgrep"
        fake.write_text(f"#!/bin/sh\nexit {pgrep_exit}\n")
        fake.chmod(0o755)
        env = dict(os.environ, HOME=str(home), PATH=f"{bin_}:{os.environ['PATH']}")
        return subprocess.run(["bash", str(SCRIPT), "clean", *cats], env=env, capture_output=True, text=True).stdout


SHOP = "@~/code/scrum/skills/trevskills-scrum/shop/machine-notes-shopmac.md\n"


class ShopMac(unittest.TestCase):
    def test_default_clean_keeps_dev_caches_only_on_the_shop_mac(self):
        self.assertNotIn("== dev-caches ==", clean(SHOP, 1))
        self.assertIn("== dev-caches ==", clean("# Global Rules\n", 1))

    def test_named_dev_caches_skipped_only_while_npm_runs(self):
        self.assertIn("[SKIP] shop Mac", clean(SHOP, 0, "dev-caches"))
        self.assertNotIn("[SKIP] shop Mac", clean(SHOP, 1, "dev-caches"))
        self.assertNotIn("[SKIP] shop Mac", clean("# Global Rules\n", 0, "dev-caches"))


if __name__ == "__main__":
    unittest.main()
