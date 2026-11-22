"""used_by in deep-audit.sh. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import json, os, subprocess, tempfile, unittest
from pathlib import Path

class UsedBy(unittest.TestCase):
    def test_used_by(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "myrepo/scrum").mkdir(parents=True); (t / "myrepo/scrum/project.md").write_text("local Docker Postgres on 5433\n")
            (t / "skills/animator").mkdir(parents=True); (t / "skills/animator/SKILL.md").write_text("renders with Blender\n")
            (t / "projects.json").write_text(json.dumps([str(t / "myrepo"), str(t / "gone")]))
            env = dict(os.environ, HOME=tmp, PROJECTS_JSON=str(t / "projects.json"), SKILL_DIRS=f"{t}/skills:{t}/nope")
            def run(name):
                return subprocess.run(["bash", str(Path(__file__).with_name("deep-audit.sh")), "usedby", name],
                                      env=env, capture_output=True, text=True).stdout.strip()
            self.assertEqual(run("Docker"), "USED BY: myrepo (scrum/project.md)")
            self.assertEqual(run("Blender"), "USED BY: animator (SKILL.md)")
            self.assertEqual(run("Zoom"), "")

    def test_used_by_dedupes_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "myrepo/scrum").mkdir(parents=True); (t / "myrepo/scrum/project.md").write_text("Docker\n")
            for d in ("a", "b"):
                (t / d / "animator").mkdir(parents=True); (t / d / "animator/SKILL.md").write_text("Docker and Blender\n")
            (t / "projects.json").write_text(json.dumps([str(t / "myrepo"), str(t / "myrepo")]))
            env = dict(os.environ, HOME=tmp, PROJECTS_JSON=str(t / "projects.json"), SKILL_DIRS=f"{t}/a:{t}/b")
            out = subprocess.run(["bash", str(Path(__file__).with_name("deep-audit.sh")), "usedby", "Docker"],
                                 env=env, capture_output=True, text=True).stdout.strip()
            self.assertEqual(out, "USED BY: myrepo (scrum/project.md), animator (SKILL.md)")

class UnusedApps(unittest.TestCase):
    def test_in_use_text_stays_on_the_app_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            for name in ("Blender", "Zoom", "Alpha", "Omega"):
                (t / f"apps/{name}.app/Contents").mkdir(parents=True)
            (t / "apps/Blender.app/Contents/big").write_bytes(b"x" * 300000)
            (t / "skills/animator").mkdir(parents=True); (t / "skills/animator/SKILL.md").write_text("renders with Blender\n")
            env = dict(os.environ, HOME=tmp, UNUSED_DAYS="-1", APPS_DIR=str(t / "apps"), PROJECTS_JSON=str(t / "none.json"), SKILL_DIRS=f"{t}/skills")
            out = subprocess.run(["bash", str(Path(__file__).with_name("deep-audit.sh")), "unusedapps"],
                                 env=env, capture_output=True, text=True).stdout.splitlines()
            blender = [l for l in out if "Blender.app" in l]
            self.assertEqual(len(blender), 1)
            self.assertIn("IN USE — do not remove. USED BY: animator (SKILL.md)", blender[0])
            self.assertEqual([l for l in out if "IN USE" in l], blender)
            self.assertNotIn("IN USE", next(l for l in out if "Zoom.app" in l))
