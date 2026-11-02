"""Tests for transcript_signals.py on synthetic transcripts.

run: python3 -m unittest discover -s global/skills/trevskills-transcript-mining -p 'test_*.py'
"""
import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transcript_signals as ts  # noqa: E402

SCRIPT = HERE / "transcript_signals.py"


def scrum_cmd(args="start 017-foo"):
    return {"type": "user", "timestamp": "2026-10-01T00:00:00Z", "message": {"role": "user", "content":
            f"<command-message>trevskills-scrum</command-message>\n<command-name>/trevskills-scrum</command-name>\n"
            f"<command-args>{args}</command-args>"}}


def asst(mid, ts_="2026-10-01T00:00:10Z", usage=None, tools=()):
    content = [{"type": "tool_use", "id": tid, "name": name, "input": inp} for tid, name, inp in tools]
    return {"type": "assistant", "timestamp": ts_, "message": {"id": mid, "role": "assistant", "content": content,
            "usage": usage or {"input_tokens": 1, "cache_creation_input_tokens": 0,
                               "cache_read_input_tokens": 0, "output_tokens": 0}}}


def result(tid, is_error, ts_="2026-10-01T00:00:20Z"):
    return {"type": "user", "timestamp": ts_, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": "x", "is_error": is_error}]}}


def user_text(text, **extra):
    return {"type": "user", "timestamp": "2026-10-01T00:00:00Z",
            "message": {"role": "user", "content": text}, **extra}


def write_jsonl(path, recs, raw_lines=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
        for line in raw_lines:
            fh.write(line + "\n")


def fake_jev(dirpath, log):
    """A jev-rank stand-in: logs each stdin line to `log`, scores every line 0.90."""
    p = Path(dirpath) / "fake-jev.py"
    p.write_text(
        "import sys\n"
        "lines=[l.rstrip('\\n') for l in sys.stdin if l.strip()]\n"
        f"open({str(log)!r},'a').write(''.join(l+'\\n' for l in lines))\n"
        "for l in lines: print('0.90\\t'+l)\n")
    return p


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.projects = self.root / "projects"
        self.projects.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              env=env or os.environ.copy())


class TestFind(Base):
    def test_classifies_scrum_and_interactive_sessions(self):
        proj = self.projects / "-repo"
        write_jsonl(proj / "s1.jsonl", [scrum_cmd("start 017-foo"), asst("m1")])
        sub = proj / "s1" / "subagents"
        write_jsonl(sub / "agent-a.jsonl", [asst(f"m{i}") for i in range(10)])
        (sub / "agent-a.meta.json").write_text(json.dumps({"agentType": "scrum-builder"}))
        write_jsonl(sub / "agent-b.jsonl", [asst("m3")])  # no meta -> unknown
        write_jsonl(proj / "s2.jsonl", [user_text("hello there"), asst("m4")])
        write_jsonl(proj / "s2" / "subagents" / "agent-c.jsonl", [asst("m5")])  # interactive child: ignored
        old = proj / "s3.jsonl"
        write_jsonl(old, [scrum_cmd("start 001-old")])
        t = time.time() - 30 * 86400
        os.utime(old, (t, t))

        got = {Path(s["path"]).name: (s["kind"], s["job"], s["role"]) for s in ts.find_sessions(self.projects, 7)}
        self.assertEqual(got, {
            "s1.jsonl": ("scrum", "017-foo", "orchestrator"),
            "agent-a.jsonl": ("scrum", "017-foo", "scrum-builder"),
            "agent-b.jsonl": ("scrum", "017-foo", "unknown"),
            "s2.jsonl": ("interactive", None, None),
        })

    def test_skips_malformed_lines(self):
        proj = self.projects / "-repo"
        write_jsonl(proj / "s1.jsonl", [], raw_lines=["{not json", "[1,2]"])
        with open(proj / "s1.jsonl", "a") as fh:
            fh.write(json.dumps(scrum_cmd("start 042-bar")) + "\n")
            fh.write("garbage\n")
            fh.write(json.dumps(asst("m1")) + "\n")
        found = ts.find_sessions(self.projects, 7)
        self.assertEqual([(s["kind"], s["job"]) for s in found], [("scrum", "042-bar")])
        self.assertEqual(ts.session_stats(proj / "s1.jsonl", "orchestrator")["turns"], 1)


class TestStats(Base):
    def test_counts_signals(self):
        u = {"input_tokens": 10, "cache_creation_input_tokens": 20, "cache_read_input_tokens": 30, "output_tokens": 40}
        grep = {"pattern": "x"}
        recs = [
            scrum_cmd(),
            # m1 appears twice (two content blocks of one message): counted once
            asst("m1", "2026-10-01T00:00:05Z", u, [("t1", "Grep", grep)]),
            asst("m1", "2026-10-01T00:00:06Z", u, [("t2", "Grep", grep)]),
            asst("m2", usage=u, tools=[(f"t{i}", "Grep", grep) for i in (3, 7, 8, 9)]),  # Grep x5 -> 1 loop
            asst("m3", usage=u, tools=[("t4", "Bash", {"command": "npm test"}),
                                       ("t5", "Bash", {"command": "npm test"}),
                                       ("t6", "Bash", {"command": "ls"})]),
            result("t4", True), result("t5", True), result("t6", True),  # npm test fails 2x; ls once
            asst("m4", usage=u, tools=[(f"r{i}", "Read", {"file_path": "/a.md", "offset": i}) for i in range(6)]
                 + [(f"q{i}", "Read", {"file_path": "/b.md"}) for i in range(5)]),
            asst("m5", usage=u, tools=[("a1", "Agent", {"subagent_type": "scrum-builder", "description": "Build"}),
                                       ("a2", "Agent", {"subagent_type": "scrum-builder", "description": "Build"}),
                                       ("a3", "Task", {"subagent_type": "scrum-check", "description": "Check"})]),
            asst("m6", "2026-10-01T00:01:40Z", u),
        ]
        p = self.projects / "-r" / "s.jsonl"
        write_jsonl(p, recs)
        st = ts.session_stats(p, "orchestrator")
        # Read /b.md x5 is also a loop (identical input 5 times)
        self.assertEqual({k: st[k] for k in ("turns", "tokens", "wall_s", "loops", "failing_cmds",
                                              "rereads", "stuck", "retries")},
                         {"turns": 6, "tokens": 600, "wall_s": 100, "loops": 2, "failing_cmds": 1,
                          "rereads": 1, "stuck": False, "retries": 1})

    def test_stuck_and_retries_role_rules(self):
        p = self.projects / "-r" / "a.jsonl"
        write_jsonl(p, [asst("m1", tools=[("w1", "Write", {"file_path": "/x/notes.txt", "content": ""}),
                                         ("a1", "Agent", {"subagent_type": "s", "description": "d"}),
                                         ("a2", "Agent", {"subagent_type": "s", "description": "d"})])]
                    + [asst(f"x{i}") for i in range(9)])
        st = ts.session_stats(p, "scrum-builder")
        self.assertTrue(st["stuck"])
        self.assertEqual(st["retries"], 0)  # retries counted for the orchestrator only
        write_jsonl(p, [asst("m1", tools=[("e1", "Edit", {"file_path": "/x/build.md"})])]
                    + [asst(f"x{i}") for i in range(9)])
        self.assertFalse(ts.session_stats(p, "scrum-builder")["stuck"])
        write_jsonl(p, [asst(f"m{i}") for i in range(10)])
        self.assertFalse(ts.session_stats(p, "general-purpose")["stuck"])

    def test_stuck_needs_min_turns(self):
        p = self.projects / "-r" / "a.jsonl"
        write_jsonl(p, [asst(f"m{i}") for i in range(9)])
        self.assertFalse(ts.session_stats(p, "scrum-builder")["stuck"])
        write_jsonl(p, [asst(f"m{i}") for i in range(10)])
        self.assertTrue(ts.session_stats(p, "scrum-builder")["stuck"])


def stat(role, path, turns=10, tokens=1000, wall_s=60, **sig):
    d = {"job": "j", "role": role, "path": path, "turns": turns, "tokens": tokens, "wall_s": wall_s,
         "loops": 0, "failing_cmds": 0, "rereads": 0, "stuck": False, "retries": 0}
    d.update(sig)
    return d


class TestOutliers(Base):
    def test_outlier_rules(self):
        stats = [
            stat("scrum-builder", "b1"), stat("scrum-builder", "b2"), stat("scrum-builder", "b5"),
            stat("scrum-builder", "b3", turns=31),  # median 10 -> 31 > 30 and > floor 30: flagged by the median rule only
            stat("scrum-builder", "b4", turns=30),  # exactly 3x and the floor: not flagged
            stat("scrum-check", "c1", tokens=1), stat("scrum-check", "c2", tokens=999999),  # 2 sessions: never median-flagged
            stat("scrum-review", "r1", loops=1),
            stat("scrum-review", "r2", stuck=True),
            stat("orchestrator", "o1", retries=2),
        ]
        self.assertEqual(sorted(o["path"] for o in ts.find_outliers(stats)), ["b3", "o1", "r1", "r2"])
        b3 = next(o for o in ts.find_outliers(stats) if o["path"] == "b3")
        self.assertIn("turns>3x median", ts.signals_text(b3))

    def test_median_needs_floor(self):
        base = [stat("r", "a"), stat("r", "b"), stat("r", "c")]
        # 25 turns: above 3x median (10) but under the 30 floor
        self.assertEqual(ts.find_outliers(base + [stat("r", "d", turns=25)]), [])
        o = ts.find_outliers(base + [stat("r", "d", turns=31)])
        self.assertEqual([x["path"] for x in o], ["d"])
        self.assertIn("turns>3x median", ts.signals_text(o[0]))

    def _loop_stats(self, tools):
        p = self.projects / "-r" / "l.jsonl"
        write_jsonl(p, [asst("m1", tools=tools)])
        return ts.session_stats(p, "scrum-builder")

    def test_loop_below_min_not_flagged(self):
        g = lambda n: [(f"t{i}", "Grep", {"pattern": "x"}) for i in range(n)]
        self.assertEqual(self._loop_stats(g(4))["loops"], 0)
        self.assertEqual(self._loop_stats(g(5))["loops"], 1)

    def test_reread_below_min_not_flagged(self):
        r = lambda n: [(f"t{i}", "Read", {"file_path": "/a.md", "offset": i}) for i in range(n)]
        self.assertEqual(self._loop_stats(r(5))["rereads"], 0)
        self.assertEqual(self._loop_stats(r(6))["rereads"], 1)


class TestCli(Base):
    def make_flailing_session(self):
        proj = self.projects / "-repo"
        write_jsonl(proj / "s1.jsonl", [scrum_cmd("start 017-foo"), asst("m1")])
        sub = proj / "s1" / "subagents"
        write_jsonl(sub / "agent-a.jsonl", [asst(f"m{i}") for i in range(10)])  # scrum- role, no .md write -> stuck
        (sub / "agent-a.meta.json").write_text(json.dumps({"agentType": "scrum-builder"}))

    def test_jev_fallback_when_missing(self):
        self.make_flailing_session()
        out = self.root / "out.md"
        r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out),
                         "--jev", str(self.root / "nope.py"))
        self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text()
        self.assertIn("Jev: unavailable", text)
        self.assertIn("- 017-foo · scrum-builder · stuck — ", text)
        top = text.split("## Top flails\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("017-foo · scrum-builder", top)

    def test_jev_used_on_outliers_only(self):
        self.make_flailing_session()
        log = self.root / "jev.log"
        out = self.root / "out.md"
        r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out),
                         "--jev", str(fake_jev(self.root, log)))
        self.assertEqual(r.returncode, 0, r.stderr)
        sent = log.read_text().splitlines()
        self.assertEqual(len(sent), 1)
        self.assertIn("scrum-builder", sent[0])
        self.assertIn("Jev: ok", out.read_text())
        self.assertIn("0.90", out.read_text().split("## Top flails", 1)[1])

    def test_no_jev_call_without_outliers(self):
        proj = self.projects / "-repo"
        write_jsonl(proj / "s1.jsonl", [scrum_cmd("start 017-foo"), asst("m1")])  # orchestrator, no signals
        log = self.root / "jev.log"
        out = self.root / "out.md"
        r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out),
                         "--jev", str(fake_jev(self.root, log)))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(log.exists())
        self.assertIn("## Outliers\nNone", out.read_text())

    def test_scrum_complaints_collected(self):
        proj = self.projects / "-repo"
        long = "the SCRUM builder keeps re-reading files " + "z" * 300
        write_jsonl(proj / "i1.jsonl", [
            user_text(long),
            user_text("scrum note but meta", isMeta=True),
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "t", "content": "scrum in a tool result"}]}},
            user_text("nothing relevant here"),
            user_text("scrum summary after compaction", isCompactSummary=True),
            user_text("scrum prompt from a script", entrypoint="sdk-cli"),
            user_text("why did scrum skip review"),
        ])
        out = self.root / "out.md"
        r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out), "--no-jev")
        self.assertEqual(r.returncode, 0, r.stderr)
        sec = out.read_text().split("## Trevor about scrum\n", 1)[1]
        items = [l for l in sec.splitlines() if l.startswith("- ")]
        self.assertEqual(len(items), 2)
        self.assertTrue(items[0].startswith("- " + long[:200]))
        self.assertNotIn(long[:201], items[0])
        self.assertIn(str(proj / "i1.jsonl"), items[0])
        self.assertTrue(items[1].startswith("- why did scrum skip review"))
        self.assertNotIn("meta", sec)
        self.assertNotIn("tool result", sec)
        self.assertNotIn("compaction", sec)
        self.assertNotIn("from a script", sec)

    def test_output_shape_and_rerun(self):
        self.make_flailing_session()
        out = self.root / "out.md"
        for _ in range(2):
            r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out), "--no-jev")
            self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text()
        lines = text.splitlines()
        self.assertEqual(lines[0], "# Transcript signals")
        self.assertRegex(lines[1], r"^Generated: \S+ · window: 7 days · scrum sessions: 2 · "
                                   r"interactive sessions: 0 · Jev: unavailable$")
        for h in ("## Per role", "## Outliers", "## Top flails", "## Trevor about scrum"):
            self.assertEqual(text.count(h + "\n"), 1, h)
        self.assertEqual(text.count("# Transcript signals"), 1)
        self.assertIn("| scrum-builder | 1 |", text)
        self.assertIn("## Trevor about scrum\nNone", text)

    def test_empty_window(self):
        out = self.root / "out.md"
        r = self.run_cli("--projects-dir", str(self.projects), "--out", str(out), "--days", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text()
        self.assertIn("window: 3 days · scrum sessions: 0 · interactive sessions: 0", text)
        for h in ("## Per role", "## Outliers", "## Top flails", "## Trevor about scrum"):
            self.assertIn(h + "\nNone", text)

    def test_default_out_missing_registry(self):
        home = self.root / "home"
        home.mkdir()
        env = dict(os.environ, HOME=str(home))
        r = self.run_cli("--projects-dir", str(self.projects), "--no-jev", env=env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("transcript_signals: no trevskills-scrum project registered; pass --out", r.stderr)
        self.assertEqual([p for p in home.rglob("*")], [])

    def test_default_out_from_registry(self):
        home = self.root / "home"
        repo = self.root / "trevskills-scrum"
        reg = home / ".claude" / "trevskills-scrum" / "projects.json"
        reg.parent.mkdir(parents=True)
        reg.write_text(json.dumps([str(self.root / "other"), str(repo)]))
        r = self.run_cli("--projects-dir", str(self.projects), "--no-jev", env=dict(os.environ, HOME=str(home)))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((repo / "scrum" / "digests" / "transcript-signals.md").is_file())


if __name__ == "__main__":
    unittest.main()
