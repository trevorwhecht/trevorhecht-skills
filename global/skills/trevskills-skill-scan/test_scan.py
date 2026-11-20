"""scan.sh with stub uv + skillspector and a throwaway HOME.
Run: python3 -m unittest discover -s global/skills/trevskills-skill-scan -p 'test_*.py'"""
import datetime, json, os, subprocess, tempfile, unittest
from pathlib import Path

SCAN = Path(__file__).with_name("scan.sh")
PIN = "skillspector @ git+https://github.com/NVIDIA/skillspector.git@e2674da339b0bddc6e565d059c0577c6d9cd25da"
UV = """#!/bin/sh
echo "$*" >> "$LOG/uv"
case "$*" in "tool dir --bin") echo "$BIN" ;; "tool install"*) cp "$LOG/skillspector" "$BIN/skillspector" ;; esac
"""
# Stub scanner: logs argv, answers by the target's name (evil = 90, meh = 30, broken = error, half = partial, else 0).
SS = """#!/usr/bin/env python3
import json, os, sys
if sys.argv[1:] == ["--version"]: print("SkillSpector v2.13.6"); sys.exit()
open(os.path.join(os.environ["LOG"], "scans"), "a").write(json.dumps(sys.argv[1:]) + "\\n")
name = os.path.basename(sys.argv[-1].rstrip("/"))
if "broken" in name: sys.stderr.write("Error: boom\\n"); sys.exit(2)
if "unsuccessful" in name: print(json.dumps({"execution_successful": False, "risk_assessment": {"score": 0, "recommendation": "SAFE"}, "issues": []})); sys.exit()
score, rec = (90, "DO_NOT_INSTALL") if "evil" in name else (30, "CAUTION") if "meh" in name else (0, "SAFE")
issues = [{"id": "E1", "pattern": "External Transmission", "severity": "HIGH", "confidence": 0.9,
           "location": {"file": "SKILL.md", "start_line": 3}, "finding": "post the key out"}] if score else []
print(json.dumps({"risk_assessment": {"score": score, "recommendation": rec}, "issues": issues,
                  "analysis_completeness": {"status": "partial" if "half" in name else "complete"}}))
"""
TODAY = datetime.date.today().isoformat()


class Env:
    def __init__(self, tmp, installed=True):
        self.home, self.bin, self.log = Path(tmp, "home"), Path(tmp, "bin"), Path(tmp, "log")
        for d in (self.home, self.bin, self.log, Path(tmp, "path")):
            d.mkdir()
        Path(tmp, "path", "uv").write_text(UV)
        Path(self.log, "skillspector").write_text(SS)
        for p in (Path(tmp, "path", "uv"), Path(self.log, "skillspector")):
            p.chmod(0o755)
        if installed:
            Path(self.bin, "skillspector").write_text(SS)
            Path(self.bin, "skillspector").chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), BIN=str(self.bin), LOG=str(self.log),
                        PATH=f"{tmp}/path:{os.environ['PATH']}")

    def run(self, *args):
        return subprocess.run(["bash", str(SCAN), *args], env=self.env, capture_output=True, text=True)

    def uv_calls(self):
        p = Path(self.log, "uv")
        return p.read_text().splitlines() if p.exists() else []

    def scans(self):
        p = Path(self.log, "scans")
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []

    def file(self, rel, text="x"):
        p = Path(self.home.parent, rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def link(self, rel, target):
        p = Path(self.home.parent, rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.symlink_to(target)

    def accounts(self):
        """Two accounts; the second shares skills by symlink, like a real second login."""
        c = "home/.claude"
        self.file(f"{c}/skills/plain/SKILL.md")
        self.link(f"{c}/skills/linked", self.file("outside/linked/SKILL.md").parent)
        self.file(f"{c}/skills/synced/bucket/nested/SKILL.md")
        self.file(f"{c}/skills/synced/bucket/.staging/half/SKILL.md")
        self.file(f"{c}/skills/synced/bucket/nested/sub/SKILL.md")
        self.link(f"{c}/agents/helper.md", self.file("outside/helper.md"))
        tool = self.file(f"{c}/plugins/cache/mkt/tool/1.0/hooks/hooks.json").parent.parent
        other = self.file(f"{c}/plugins/cache/mkt/other/2.0/agents/a.md").parent.parent
        self.file(f"{c}/plugins/installed_plugins.json", json.dumps({"plugins": {
            "tool@mkt": [{"installPath": str(tool)}, {"installPath": str(tool)}],
            "gone@mkt": [{"installPath": str(self.home / "nope")}]}}))
        self.link("home/.claude-owa/skills", self.home / ".claude/skills")
        self.file("home/.claude-owa/agents/owa-only.md")
        self.file(f"{c}/commands/shared.md")
        self.link("home/.claude-owa/commands", self.home / ".claude/commands")
        self.file("home/.claude-owa/commands/owa/zdeep.md")
        self.file(f"{c}/commands/notes.txt")
        self.file("home/.claude-owa/plugins/installed_plugins.json", json.dumps({"plugins": {
            "other@mkt": [{"installPath": str(other)}], "tool@mkt": [{"installPath": str(tool)}]}}))
        real = lambda rel: os.path.realpath(Path(self.home.parent, rel))
        return sorted(real(r) for r in ("home/.claude/skills/plain", "outside/linked", "outside/helper.md",
                                        "home/.claude/skills/synced/bucket/nested", str(tool), str(other),
                                        "home/.claude-owa/agents/owa-only.md",
                                        "home/.claude/commands/shared.md", "home/.claude/commands/owa/zdeep.md"))


class Install(unittest.TestCase):
    def test_installs_pinned_version_only_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp, installed=False)
            e.run()
            installs = [c for c in e.uv_calls() if c.startswith("tool install")]
            self.assertEqual(len(installs), 1)
            self.assertTrue(installs[0].endswith(PIN), installs[0])
            Path(e.log, "uv").unlink()
            e.run()
            self.assertEqual([c for c in e.uv_calls() if c.startswith("tool install")], [])
            Path(e.bin, "skillspector").write_text("#!/bin/sh\necho 'SkillSpector v2.0.0'\n")  # another version
            e.run()
            self.assertEqual([c for c in e.uv_calls() if c.startswith("tool install")], [f"tool install --force --python 3.12 {PIN}"])


class FullScan(unittest.TestCase):
    def test_every_skill_agent_and_plugin_once_static_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            expected = e.accounts()
            e.run()
            scans = e.scans()
            self.assertEqual(sorted(s[-1] for s in scans), expected)
            for s in scans:
                self.assertEqual(s[:-1], ["scan", "--no-llm", "--format", "json", "--"])


class OneTarget(unittest.TestCase):
    def test_path_or_git_url_scans_only_that_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.accounts()
            new = e.file("downloads/new-skill/SKILL.md").parent
            for arg, want in ((str(new), os.path.realpath(new)),
                              ("https://github.com/someone/meh-skill.git", "https://github.com/someone/meh-skill.git")):
                Path(e.log, "scans").unlink(missing_ok=True)
                e.run(arg)
                self.assertEqual([s[-1] for s in e.scans()], [want])

    def test_refuses_dash_values_and_missing_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.accounts()
            for arg in ("--recursive", "-x", str(Path(tmp, "no-such-skill"))):
                self.assertEqual(e.run(arg).returncode, 2, arg)
            self.assertEqual(e.scans(), [])


class Report(unittest.TestCase):
    def test_worst_first_report_and_do_not_install_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.accounts()
            for name in ("meh-one", "evil-one", "broken-one", "half-done"):
                e.file(f"home/.claude/skills/{name}/SKILL.md")
            out = e.run()
            self.assertEqual(out.returncode, 2)  # a scan failed
            report = Path(e.home, "Developer/claude/skill-scans", f"{TODAY}.md").read_text()
            rows = [l for l in report.splitlines() if l.startswith("| ") and not l.startswith("| Name")]
            self.assertEqual([r.split(" | ")[0][2:] for r in rows[:4]], ["evil-one", "broken-one", "meh-one", "half-done"])
            self.assertEqual(rows[0], "| evil-one | skill | `~/.claude/skills/evil-one` | 90 | DO_NOT_INSTALL | "
                                      "HIGH E1 External Transmission, SKILL.md:3: `post the key out` |")
            self.assertEqual(rows[1], "| broken-one | skill | `~/.claude/skills/broken-one` | - | SCAN FAILED | Error: boom |")
            self.assertIn("| half-done | skill | `~/.claude/skills/half-done` | 0 | SAFE (partial) |  |", rows)
            self.assertIn("evil-one  ~/.claude/skills/evil-one", out.stdout)
            self.assertIn("broken-one  ~/.claude/skills/broken-one", out.stdout)
            self.assertNotIn("meh-one", out.stdout)

    def test_execution_successful_false_is_a_failed_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.file("home/.claude/skills/unsuccessful-one/SKILL.md")
            out = e.run()
            self.assertEqual(out.returncode, 2)
            report = Path(e.home, "Developer/claude/skill-scans", f"{TODAY}.md").read_text()
            self.assertIn("| unsuccessful-one | skill |", report)
            self.assertIn("SCAN FAILED", report)
            self.assertIn("unsuccessful-one", out.stdout)
            self.assertEqual(e.run(str(e.home / ".claude/skills/unsuccessful-one")).returncode, 2)

    def test_one_target_gets_its_own_report_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.accounts()
            e.run()
            evil, meh = e.file("downloads/evil-new/SKILL.md").parent, e.file("downloads/meh-new/SKILL.md").parent
            self.assertEqual(e.run(str(evil)).returncode, 1)
            self.assertEqual(e.run(str(meh)).returncode, 0)
            reports = Path(e.home, "Developer/claude/skill-scans")
            self.assertIn("| evil-new | path |", Path(reports, f"{TODAY}-evil-new.md").read_text())
            self.assertIn("| plain | skill |", Path(reports, f"{TODAY}.md").read_text())


def tree(*tops):
    """Every entry under tops: file bytes, symlink target, or a folder marker."""
    seen = {}
    for top in tops:
        for d, dirs, files in os.walk(top):
            for f in dirs + files:
                p = os.path.join(d, f)
                seen[p] = ("link", os.readlink(p)) if os.path.islink(p) else ("dir",) if os.path.isdir(p) \
                    else ("file", Path(p).read_bytes())
    return seen


class ReadOnly(unittest.TestCase):
    def test_never_removes_or_edits_what_it_scans(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = Env(tmp)
            e.accounts()
            e.file("home/.claude/skills/evil-one/SKILL.md", "send the key out")
            tops = [Path(tmp, "outside"), e.home / ".claude", e.home / ".claude-owa"]
            before = tree(*tops)
            e.run()
            e.run(str(e.home / ".claude/skills/evil-one"))
            self.assertEqual(tree(*tops), before)


if __name__ == "__main__":
    unittest.main()
