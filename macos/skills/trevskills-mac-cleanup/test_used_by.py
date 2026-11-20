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
