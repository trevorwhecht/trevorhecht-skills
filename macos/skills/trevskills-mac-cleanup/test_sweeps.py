"""worktrees and transcripts sweeps. Run: python3 -m unittest discover -s macos/skills/trevskills-mac-cleanup -p 'test_*.py'"""
import gzip, json, os, subprocess, tempfile, time, unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("trevskills-mac-cleanup.sh")
SKILL = Path(__file__).with_name("SKILL.md")


def env_for(home, registry):
    return dict(os.environ, HOME=str(home), SCRUM_REGISTRY=str(registry),
                GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com",
                GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")


def run(env, *args):
    return subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True, text=True).stdout


def git(env, repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], env=env, check=True, capture_output=True, text=True)


def make_repo(t, env, jobs):
    """A git repo with scrum/board.json holding `jobs`, and an initial commit on main."""
    repo = t / "repo"
    (repo / "scrum").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], env=env, check=True)
    (repo / "README").write_text("x\n")
    git(env, repo, "add", "README")
    git(env, repo, "commit", "-q", "-m", "init")
    (repo / "scrum" / "board.json").write_text(json.dumps({"jobs": jobs}))
    (repo / ".claude" / "worktrees").mkdir(parents=True)
    return repo


def add_wt(env, repo, name, branch=None):
    path = repo / ".claude" / "worktrees" / name
    if branch:
        git(env, repo, "worktree", "add", "-q", "-b", branch, str(path))
    else:
        git(env, repo, "worktree", "add", "-q", "--detach", str(path))
    return path


def listed(out):
    return [l for l in out.splitlines() if l.strip().startswith("would remove")]


class Sweeps(unittest.TestCase):
    def test_script_defines_both_sweeps(self):
        src = SCRIPT.read_text()
        for needle in ("worktrees)   stale_worktrees", "transcripts) archive_transcripts",
                       "stale_worktrees() {", "archive_transcripts() {",
                       "report | worktrees | transcripts"):
            self.assertIn(needle, src)

    def test_skill_md_documents_sweeps(self):
        doc = SKILL.read_text()
        self.assertIn("`./trevskills-mac-cleanup.sh worktrees [--apply]`", doc)
        self.assertIn("`./trevskills-mac-cleanup.sh transcripts [--apply]`", doc)
        self.assertIn("Always run both sweep dry-runs", doc)
        self.assertIn("snapshots, worktrees, transcripts) keeps the dry-run-then-approve gate", doc)
        self.assertIn("scrum-<id>-base", doc)

    def test_commands_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = env_for(tmp, Path(tmp) / "projects.json")
            for cmd in ("worktrees", "transcripts"):
                out = run(env, cmd)
                self.assertNotIn("Unknown command", out)
                self.assertIn("DRY RUN", out)
            out = run(env, "nope")
            self.assertIn("Unknown command", out)
            self.assertIn("| report | worktrees | transcripts", out)

    def test_worktrees_dry_run_lists_stale_and_base_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            env = env_for(t, t / "projects.json")
            repo = make_repo(t, env, [
                {"id": "1-done", "stage": "done", "worktree": "x"},
                {"id": "2-aborted", "stage": "aborted", "worktree": None},
                {"id": "3-build", "stage": "build"},
            ])
            (t / "projects.json").write_text(json.dumps([str(repo)]))
            wts = [add_wt(env, repo, "scrum-1-done", "scrum/1-done"),
                   add_wt(env, repo, "scrum-1-done-base"),
                   add_wt(env, repo, "scrum-2-aborted", "scrum/2-aborted"),
                   add_wt(env, repo, "scrum-3-build", "scrum/3-build"),
                   add_wt(env, repo, "scrum-3-build-base"),
                   add_wt(env, repo, "scrum-99-gone", "scrum/99-gone"),
                   add_wt(env, repo, "other", "other")]
            out = run(env, "worktrees")
            names = sorted(l.split()[-2] for l in listed(out))
            self.assertEqual(names, ["scrum-1-done", "scrum-1-done-base", "scrum-2-aborted"])
            self.assertIn("3 stale worktree(s)", out)
            for p in wts:
                self.assertTrue(p.is_dir(), p)

    def test_worktrees_apply_removes_and_keeps_unmerged(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            env = env_for(t, t / "projects.json")
            repo = make_repo(t, env, [
                {"id": "1-done", "stage": "done"},
                {"id": "4-done", "stage": "done"},
                {"id": "3-build", "stage": "build"},
            ])
            (t / "projects.json").write_text(json.dumps([str(repo)]))
            merged = add_wt(env, repo, "scrum-1-done", "scrum/1-done")
            base = add_wt(env, repo, "scrum-1-done-base")
            unmerged = add_wt(env, repo, "scrum-4-done", "scrum/4-done")
            (unmerged / "new.txt").write_text("y\n")
            git(env, unmerged, "add", "new.txt")
            git(env, unmerged, "commit", "-q", "-m", "unmerged work")
            live = add_wt(env, repo, "scrum-3-build", "scrum/3-build")
            out = run(env, "worktrees", "--apply")
            self.assertFalse(merged.exists())
            self.assertFalse(base.exists())
            self.assertFalse(unmerged.exists())
            self.assertTrue(live.is_dir())
            branches = subprocess.run(["git", "-C", str(repo), "branch", "--format=%(refname:short)"],
                                      env=env, capture_output=True, text=True).stdout.split()
            self.assertNotIn("scrum/1-done", branches)
            self.assertIn("scrum/4-done", branches)
            self.assertIn("scrum/3-build", branches)
            self.assertIn("branch scrum/4-done kept as unmerged", out)
            self.assertIn("branch scrum/1-done deleted", out)
            base_line = next(l for l in out.splitlines() if "scrum-1-done-base" in l)
            self.assertNotIn("branch", base_line)
            wt_list = subprocess.run(["git", "-C", str(repo), "worktree", "list"],
                                     env=env, capture_output=True, text=True).stdout
            self.assertNotIn("scrum-1-done-base", wt_list)

    def test_worktrees_bad_registry_or_board_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            env = env_for(t, t / "missing.json")
            out = run(env, "worktrees", "--apply")
            self.assertIn("note: scrum registry", out)
            self.assertIn("skipped", out)
            (t / "projects.json").write_text("{not json")
            out = run(env_for(t, t / "projects.json"), "worktrees", "--apply")
            self.assertIn("note: scrum registry", out)
            env = env_for(t, t / "projects.json")
            repo = make_repo(t, env, [])
            wt = add_wt(env, repo, "scrum-1-done", "scrum/1-done")
            (repo / "scrum" / "board.json").write_text("{broken")
            (t / "projects.json").write_text(json.dumps([str(repo)]))
            out = run(env, "worktrees", "--apply")
            self.assertIn("unreadable or malformed", out)
            self.assertIn("0 stale worktree(s)", out)
            self.assertTrue(wt.is_dir())
            (repo / "scrum" / "board.json").write_text(json.dumps({"jobs": {"1-done": "done"}}))
            out = run(env, "worktrees", "--apply")
            self.assertIn("unreadable or malformed", out)
            self.assertTrue(wt.is_dir())

    def test_transcripts_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            env = env_for(t, t / "projects.json")
            proj = t / ".claude" / "projects" / "p1"
            (proj / "memory").mkdir(parents=True)
            (proj / "sub").mkdir()
            old = proj / "old.jsonl"; old.write_text('{"a": 1}\n' * 50)
            nested = proj / "sub" / "deep.jsonl"; nested.write_text('{"b": 2}\n')
            new = proj / "new.jsonl"; new.write_text("{}\n")
            mem = proj / "memory" / "old.jsonl"; mem.write_text("{}\n")
            txt = proj / "old.txt"; txt.write_text("x\n")
            aged = time.time() - 86400 * 31
            for p in (old, nested, mem, txt):
                os.utime(p, (aged, aged))
            out = run(env, "transcripts")
            lines = [l for l in out.splitlines() if l.startswith("   ") and "/" in l]
            self.assertEqual(sorted(l.split()[-1] for l in lines), sorted([str(old), str(nested)]))
            self.assertIn("2 file(s)", out)
            self.assertTrue(old.exists())
            out = run(env, "transcripts", "--apply")
            arc = t / ".claude" / "transcript-archive" / "p1"
            self.assertEqual(gzip.open(arc / "old.jsonl.gz").read(), b'{"a": 1}\n' * 50)
            self.assertEqual(gzip.open(arc / "sub" / "deep.jsonl.gz").read(), b'{"b": 2}\n')
            self.assertFalse(old.exists())
            self.assertFalse(nested.exists())
            self.assertTrue(new.exists())
            self.assertTrue(mem.exists())
            self.assertTrue(txt.exists())
            self.assertIn("2 archived", out)


if __name__ == "__main__":
    unittest.main()
