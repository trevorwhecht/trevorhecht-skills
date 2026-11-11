"""Tests for prospect.py: CLI runs on a temp project, a stub ingest server, a fake docker on PATH.

run: python3 -m unittest discover -s global/skills/trevskills-prospect -p 'test_*.py'
"""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "prospect.py"
sys.path.insert(0, str(HERE))
import prospect  # noqa: E402

LAT, LON = 47.6205, -122.3493
OPT_OUT_LINE = "If you'd rather not hear from me, just reply and I won't email again."
WEEK = {d: ["9 AM-5 PM"] for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")}


def profile(**over):
    p = {
        "business": "Example Tee Co screen printing",
        "targets": [{"category": "Churches", "keywords": ["church", "school"]},
                    {"category": "Leagues", "keywords": ["School", "sports league"]}],
        "center": f"{LAT},{LON}",
        "radius_miles": 5,
        "conversion_pct": 5,
        "avg_order_value": 400,
        "goal_jobs": 3,
        "max_results": 100,
        "outreach": "find",
        "site_url": "http://127.0.0.1:9",
    }
    p.update(over)
    return p


def row(i, dlat=0.005, **over):
    r = {"id": f"place{i}", "title": f"Business {i}", "category": "Church", "address": f"{i} Main St",
         "website": f"https://b{i}.example", "phone": f"(206) 555-01{i:02d}", "emails": [f"hi@b{i}.example"],
         "rating": 4.5, "review_count": 20 + i, "open_hours": WEEK, "latitude": LAT + dlat * (i + 1),
         "longitude": LON, "status": ""}
    r.update(over)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.proj = self.base / "proj"
        (self.proj / "prospect").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items() if k != "LEADS_AGENT_TOKEN"}

    def write_profile(self, **over):
        (self.proj / "prospect" / "profile.json").write_text(json.dumps(profile(**over)))

    def write_json(self, name, data):
        p = self.base / name
        p.write_text(json.dumps(data))
        return p

    def run_cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True,
                              text=True, env=env or self.env)

    def assert_one_line_error(self, r, code, text=None):
        self.assertEqual(r.returncode, code, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(len(r.stderr.strip().splitlines()), 1, r.stderr)
        self.assertTrue(r.stderr.startswith("prospect: "), r.stderr)
        if text:
            self.assertEqual(r.stderr.strip(), text)


class PlanTest(Base):
    def test_plan_math_and_overrides(self):
        self.write_profile()
        r = self.run_cli("plan", self.proj, "--set", "radius_miles=2", "--set", "business_address=1 Elm St, Town")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["center"], [47.6205, -122.3493])
        self.assertEqual(out["radius_m"], 3219)
        self.assertEqual(out["queries"], ["church", "school", "sports league"])
        self.assertEqual(out["leads_needed"], 60)  # 3 / 5% exactly, not 61 from float error
        self.assertEqual(out["ev_per_lead_at_fit_100"], 20.0)

    def test_plan_bare_name_resolves_under_developer_repos(self):
        proj = self.base / "home" / "Developer" / "repos" / "shop"
        (proj / "prospect").mkdir(parents=True)
        (proj / "prospect" / "profile.json").write_text(json.dumps(profile(goal_jobs=1, conversion_pct=10)))
        r = self.run_cli("plan", "shop", env={**self.env, "HOME": str(self.base / "home")})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["leads_needed"], 10)

    def test_plan_rejects_bad_profile(self):
        self.assert_one_line_error(self.run_cli("plan", self.proj), 2)  # missing file
        bad = profile()
        del bad["goal_jobs"]
        (self.proj / "prospect" / "profile.json").write_text(json.dumps(bad))
        self.assert_one_line_error(self.run_cli("plan", self.proj), 2, "prospect: profile is missing goal_jobs")
        cases = [
            ({"radius_miles": "far"}, "radius_miles"),
            ({"radius_miles": True}, "radius_miles"),
            ({"conversion_pct": 150}, "conversion_pct"),
            ({"max_results": 501}, "max_results"),
            ({"goal_jobs": 1.5}, "goal_jobs"),
            ({"must_have_contact": ["fax"]}, "must_have_contact"),
            ({"outreach": "draft"}, "business_address"),
            ({"site_url": "ftp://x"}, "site_url"),
            ({"site_url": "http://example.com"}, "site_url"),
            ({"site_url": "http://localhost.example.com"}, "site_url"),
            ({"targets": []}, "targets"),
            ({"min_rating": 6}, "min_rating"),
            ({"center": "95,10"}, "center"),
        ]
        for over, key in cases:
            with self.subTest(over=over):
                self.write_profile(**over)
                r = self.run_cli("plan", self.proj)
                self.assert_one_line_error(r, 2)
                self.assertIn(key, r.stderr)
        for ok in ("https://example.com", "http://localhost:3000", "http://127.0.0.1:8080"):
            with self.subTest(ok=ok):
                self.write_profile(site_url=ok)
                r = self.run_cli("plan", self.proj)
                self.assertEqual(r.returncode, 0, r.stderr)
        self.write_profile()
        r = self.run_cli("plan", self.proj, "--set", "radius_mile=3")
        self.assert_one_line_error(r, 2, "prospect: unknown key radius_mile")
        r = self.run_cli("plan", self.proj, "--set", "noequals")
        self.assert_one_line_error(r, 2)

    def test_example_profile_is_valid(self):
        shutil.copy(HERE / "profile.example.json", self.proj / "prospect" / "profile.json")
        r = self.run_cli("plan", self.proj)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["queries"])


class CheckTest(Base):
    def setUp(self):
        super().setUp()
        self.write_profile()

    def check(self, rows):
        r = self.run_cli("check", self.write_json("raw.json", rows), "--project", self.proj)
        return r, json.loads(r.stdout)

    def test_check_flags_broken_fields(self):
        rows = [row(i, rating=0, review_count=0, open_hours={"Monday": ["9 AM-5 PM"]}) for i in range(6)]
        rows[0]["phone"], rows[1]["phone"] = "12", "call us"
        rows[5]["latitude"] = LAT + 0.2  # ~13.8 mi, radius is 5
        r, rep = self.check(rows)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertEqual({t["field"] for t in rep["tripped"]},
                         {"rating", "review_count", "open_hours", "phone", "distance"})
        self.assertTrue(all(t["why"] for t in rep["tripped"]))
        self.assertFalse(rep["wholesale"])
        self.assertEqual(rep["rows"], 6)
        self.assertEqual(rep["fill"]["website"], 1.0)

    def test_check_clean_fixture_passes(self):
        rows = [row(i) for i in range(6)]
        rows[2]["website"] = ""
        r, rep = self.check(rows)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(rep["tripped"], [])
        self.assertFalse(rep["wholesale"])
        self.assertAlmostEqual(rep["fill"]["website"], 5 / 6, places=3)
        self.assertEqual(set(rep["fill"]), {"id", "title", "category", "address", "website", "phone", "emails",
                                            "rating", "review_count", "open_hours", "latitude", "longitude"})

    def test_check_wholesale_on_empty_and_missing_ids(self):
        r, rep = self.check([])
        self.assertEqual(r.returncode, 3)
        self.assertTrue(rep["wholesale"])
        rows = [row(i) for i in range(6)]
        for x in rows[:4]:
            x["id"] = ""
        r, rep = self.check(rows)
        self.assertEqual(r.returncode, 3)
        self.assertTrue(rep["wholesale"])
        r, rep = self.check([row(i, website="", phone="", emails=[]) for i in range(5)])
        self.assertEqual(r.returncode, 3)
        self.assertTrue(rep["wholesale"])
        self.assertEqual({t["field"] for t in rep["tripped"]}, {"website", "phone", "emails"})


class FilterTest(Base):
    def run_filter(self, rows, *extra):
        out = self.base / "cand.json"
        r = self.run_cli("filter", self.write_json("raw.json", rows), "--project", self.proj, "--out", out, *extra)
        return r, out

    def test_filter_drops_and_counts_each_reason(self):
        self.write_profile(exclude_categories=["tattoo"], exclude_chains=["starbucks"], min_rating=4,
                           max_results=2)
        rows = [
            row(1, phone="206.555.0101"),
            row(1, title="dupe of 1"),
            row(2),
            row(3),
            row(4, status="Permanently closed"),
            row(5, category="Tattoo Shop"),
            row(6, title="STARBUCKS Reserve"),
            row(7, latitude=LAT + 0.2),
            row(8, rating=3.0),
            row(9, phone="", emails=[], website=""),
            row(10, phone="12", emails=[], website=""),
        ]
        r, out = self.run_filter(rows)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["dropped"], {
            "duplicate": 1, "closed": 1, "excluded category": 1, "chain": 1, "outside radius": 1,
            "below min rating": 1, "no contact": 2, "over max results": 1})
        data = json.loads(out.read_text())
        self.assertEqual([x["id"] for x in data["rows"]], ["place1", "place2"])
        self.assertEqual(data["rows"][0]["phone"], "+12065550101")
        self.assertEqual(data["rows"][0]["title"], "Business 1")
        self.assertEqual(data["rows"][0]["distance_mi"], 0.69)
        self.assertEqual(data["found"], 11)

    def test_filter_drop_fields_removes_them_everywhere(self):
        self.write_profile(min_rating=4)
        rows = [row(i) for i in range(5)] + [row(5, rating=3.0)]
        r, out = self.run_filter(rows, "--drop-fields", "rating,open_hours")
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(out.read_text())["rows"]
        self.assertEqual(len(got), 6)  # min_rating not applied once rating is dropped
        for x in got:
            self.assertNotIn("rating", x)
            self.assertNotIn("open_hours", x)
        r, out = self.run_filter(rows, "--drop-fields", "phone,emails,website")
        self.assertEqual(json.loads(r.stdout)["dropped"], {"below min rating": 1, "no contact": 5})

    def test_filter_skips_distance_when_coords_dropped(self):
        self.write_profile()
        rows = [row(1), row(2, latitude=LAT + 0.2)]  # place2 is ~13.8 mi, radius is 5
        r, _ = self.run_filter(rows)
        self.assertEqual(json.loads(r.stdout)["dropped"], {"outside radius": 1})
        for field in ("latitude", "longitude"):
            with self.subTest(field=field):
                r, out = self.run_filter(rows, "--drop-fields", field)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(json.loads(r.stdout)["dropped"], {})
                got = json.loads(out.read_text())["rows"]
                self.assertEqual(sorted(x["id"] for x in got), ["place1", "place2"])
                for x in got:
                    self.assertNotIn("distance_mi", x)

    def test_filter_refuses_wholesale_failure(self):
        self.write_profile()
        r, out = self.run_filter([])
        self.assert_one_line_error(r, 3)
        self.assertFalse(out.exists())


class Stub:
    """Records POST headers and bodies; answers with `status` and `body`."""

    def __init__(self, status=200, body=b'{"ok":true}'):
        self.calls, stub = [], self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers["Content-Length"])
                stub.calls.append((self.path, self.headers["Authorization"], json.loads(self.rfile.read(n))))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class IngestTest(Base):
    def setUp(self):
        super().setUp()
        self.stub = Stub()
        self.addCleanup(self.stub.close)

    def ingest(self, cands, scores, *extra, env=None, **prof):
        self.write_profile(site_url=self.stub.url, **prof)
        c = self.write_json("cand.json", {"found": len(cands) + 2, "dropped": {"chain": 2}, "rows": cands})
        s = self.write_json("scores.json", scores)
        return self.run_cli("ingest", self.proj, "--candidates", c, "--scores", s, *extra, env=env)

    def leads(self):
        return [lead for _, _, body in self.stub.calls for lead in body["leads"]]

    def test_ingest_dry_run_prints_ranked_leads_and_posts_nothing(self):
        cands = [dict(row(1, phone="+12065550101"), distance_mi=0.35),
                 dict(row(2, phone="+12065550102"), distance_mi=0.69), dict(row(3), distance_mi=1.0)]
        scores = [{"id": "place1", "fit": 40, "reason": "small parish"},
                  {"id": "place2", "fit": 90, "reason": "runs a youth league"}]
        r = self.ingest(cands, scores, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.stub.calls, [])
        lines = r.stdout.strip().splitlines()
        self.assertEqual(lines[0], "1. fit 90  ev $18  Business 2  0.69 mi  hi@b2.example  — runs a youth league")
        self.assertEqual(lines[1], "2. fit 40  ev $8  Business 1  0.35 mi  hi@b1.example  — small parish")
        self.assertEqual(lines[-1], "found 5 · dropped: chain 2, unscored 1 · would ingest 2 · drafts 0 · "
                                    "leads to goal 58")

    def test_ingest_posts_contract_body_in_batches(self):
        cands = [dict(row(i, phone="+12065550100"), distance_mi=1.5) for i in range(205)]
        cands[0] = {"id": "place0", "title": "Bare Shop", "phone": "+12065550100", "distance_mi": 0.0,
                    "rating": None}
        scores = [{"id": f"place{i}", "fit": 50, "reason": "fits"} for i in range(1, 205)]
        scores.append({"id": "place0", "fit": 99.6, "reason": "best fit", "draft": "ignored in find mode"})
        r = self.ingest(cands, scores, env={**self.env, "LEADS_AGENT_TOKEN": "tok-123"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([len(b["leads"]) for _, _, b in self.stub.calls], [200, 5])
        self.assertEqual({(p, a) for p, a, _ in self.stub.calls}, {("/api/leads/ingest", "Bearer tok-123")})
        leads = self.leads()
        self.assertEqual(leads[0], {"source": "prospect", "placeId": "place0", "name": "Bare Shop",
                                    "company": "Bare Shop", "phone": "+12065550100", "distanceMi": 0.0,
                                    "summary": "best fit", "conversionProbability": 100})
        self.assertEqual(leads[1], {
            "source": "prospect", "placeId": "place1", "name": "Business 1", "company": "Business 1",
            "email": "hi@b1.example", "phone": "+12065550100", "website": "https://b1.example",
            "address": "1 Main St", "category": "Church", "distanceMi": 1.5, "rating": 4.5, "reviewCount": 21,
            "summary": "fits", "conversionProbability": 50})
        self.assertIn("ingested 205", r.stdout)
        self.assertIn("leads to goal 0", r.stdout)

    def test_ingest_stops_on_http_error(self):
        self.stub.close()
        self.stub = Stub(status=422, body=b'{"error":"bad\nlead"}')
        r = self.ingest([row(1)], [{"id": "place1", "fit": 50, "reason": "x"}],
                        env={**self.env, "LEADS_AGENT_TOKEN": "tok-123"})
        self.assert_one_line_error(r, 1)
        self.assertIn("422", r.stderr)
        self.assertIn("bad lead", r.stderr)

    def test_ingest_without_token_stops_before_posting(self):
        r = self.ingest([row(1)], [{"id": "place1", "fit": 50, "reason": "x"}])
        self.assert_one_line_error(r, 2, "prospect: LEADS_AGENT_TOKEN is not set")
        self.assertEqual(self.stub.calls, [])
        (self.proj / ".env.local").write_text("LEADS_AGENT_TOKEN=\n")
        r = self.ingest([row(1)], [{"id": "place1", "fit": 50, "reason": "x"}])
        self.assert_one_line_error(r, 2, "prospect: LEADS_AGENT_TOKEN is not set")
        self.assertEqual(self.stub.calls, [])

    def test_token_read_from_env_local_and_never_printed(self):
        (self.proj / ".env.local").write_text('OTHER=1\nLEADS_AGENT_TOKEN="sekrit-file-tok"\n')
        r = self.ingest([row(1)], [{"id": "place1", "fit": 50, "reason": "x"}])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.stub.calls[0][1], "Bearer sekrit-file-tok")
        self.assertNotIn("sekrit", r.stdout + r.stderr)
        # an error body that echoes the token is scrubbed too
        self.stub.close()
        self.stub = Stub(status=401, body=b"bad token sekrit-file-tok")
        r = self.ingest([row(1)], [{"id": "place1", "fit": 50, "reason": "x"}])
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("sekrit", r.stdout + r.stderr)

    def test_drafts_capped_at_30_with_footer_and_only_with_email(self):
        cands = [dict(row(i), distance_mi=1.0) for i in range(36)]
        cands[0]["emails"], cands[1]["emails"] = [], []
        scores = [{"id": f"place{i}", "fit": 100 - i, "reason": "r", "draft": f"Hi {i},\nWe print shirts.\n"}
                  for i in range(36)]
        r = self.ingest(cands, scores, env={**self.env, "LEADS_AGENT_TOKEN": "t"}, outreach="draft",
                        business_address="100 Example Ave, Springfield, ST 00000")
        self.assertEqual(r.returncode, 0, r.stderr)
        leads = self.leads()
        with_draft = [x["placeId"] for x in leads if "draftMessage" in x]
        self.assertEqual(with_draft, [f"place{i}" for i in range(2, 32)])
        self.assertEqual(leads[2]["draftMessage"], "Hi 2,\nWe print shirts.\n\n100 Example Ave, Springfield, ST 00000\n"
                                                   + OPT_OUT_LINE)
        self.assertIn("drafts 30", r.stdout)

    def test_build_lead_omits_zero_rating_and_review_count(self):
        score = {"fit": 50, "reason": "r"}
        for zero in ({"rating": 0, "review_count": 0}, {"rating": None, "review_count": None}, {}):
            with self.subTest(zero=zero):
                r = row(1)
                del r["rating"], r["review_count"]
                lead = prospect.build_lead({**r, **zero}, score)
                self.assertNotIn("rating", lead)
                self.assertNotIn("reviewCount", lead)
        lead = prospect.build_lead(row(1, rating=4.5, review_count=21), score)
        self.assertEqual((lead["rating"], lead["reviewCount"]), (4.5, 21))

    def test_find_mode_sends_no_drafts(self):
        cands = [dict(row(i), distance_mi=1.0) for i in range(3)]
        scores = [{"id": f"place{i}", "fit": 50, "reason": "r", "draft": "Hello"} for i in range(3)]
        r = self.ingest(cands, scores, env={**self.env, "LEADS_AGENT_TOKEN": "t"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.leads()), 3)
        self.assertFalse(any("draftMessage" in x for x in self.leads()))
        self.assertIn("drafts 0", r.stdout)


FAKE_DOCKER = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
if args[0] == "info":
    sys.exit(0 if os.environ["FAKE_DOCKER"] == "up" else 1)
mount = args[args.index("-v") + 1]
host, _, box = mount.partition(":")
local = lambda p: os.path.join(host, os.path.relpath(p, box))
queries = open(local(args[args.index("-input") + 1])).read()
json.dump({{"argv": args, "queries": queries}}, open(os.environ["FAKE_LOG"], "w"))
rows = [{{"place_id": "ChIJ1", "title": "One", "category": "", "categories": ["Church", "Preschool"], "web_site": "https://one.example", "longtitude": -122.3,
         "latitude": 47.6, "review_rating": 4.1, "review_count": 9, "emails": ["a@one.example"]}},
        {{"data_id": "0x2", "title": "Two", "phone": "206-555-0100"}}]
with open(local(args[args.index("-results") + 1]), "w") as f:
    f.write("\\n".join(json.dumps(r) for r in rows))
"""


class ScrapeTest(Base):
    def setUp(self):
        super().setUp()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name, body in (("docker", FAKE_DOCKER),
                           ("open", f"#!{sys.executable}\nimport os,sys\n"
                                    f"open(os.environ['FAKE_OPEN'],'w').write(' '.join(sys.argv[1:]))\n")):
            (self.bin / name).write_text(body)
            (self.bin / name).chmod(0o755)
        self.log, self.opened = self.base / "docker.json", self.base / "open.txt"
        p = mock.patch.dict(os.environ, {"PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                                         "FAKE_LOG": str(self.log), "FAKE_OPEN": str(self.opened),
                                         "FAKE_DOCKER": "up"})
        p.start()
        self.addCleanup(p.stop)
        self.write_profile()

    def main(self, *args):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = prospect.main([str(a) for a in args])
        return code, err.getvalue()

    def test_scrape_builds_docker_command(self):
        out = self.base / "raw.json"
        code, err = self.main("scrape", self.proj, "--out", out)
        self.assertEqual(code, 0, err)
        log = json.loads(self.log.read_text())
        argv = log["argv"]
        self.assertEqual(argv[0], "run")
        self.assertIn("gosom/google-maps-scraper:v1.18.2", argv)
        after = lambda flag: argv[argv.index(flag) + 1]
        self.assertEqual(after("-geo"), "47.6205,-122.3493")
        self.assertEqual(after("-radius"), "8047")
        self.assertEqual(after("-exit-on-inactivity"), "3m")
        for flag in ("-json", "-email", "-fast-mode"):
            self.assertIn(flag, argv)
        self.assertEqual(log["queries"].split("\n"), ["church", "school", "sports league"])
        rows = json.loads(out.read_text())
        self.assertEqual(rows[0]["id"], "ChIJ1")
        self.assertEqual(rows[0]["website"], "https://one.example")
        self.assertEqual(rows[0]["longitude"], -122.3)
        self.assertEqual(rows[0]["rating"], 4.1)
        self.assertEqual(rows[0]["category"], "Church, Preschool")
        self.assertEqual(rows[1]["id"], "0x2")
        self.assertEqual(rows[1]["phone"], "206-555-0100")
        self.assertFalse(self.opened.exists())
        code, err = self.main("scrape", self.proj, "--out", out, "--set", "fast_mode=false")
        self.assertEqual(code, 0, err)
        self.assertNotIn("-fast-mode", json.loads(self.log.read_text())["argv"])

    def test_scrape_stops_when_docker_never_starts(self):
        os.environ["FAKE_DOCKER"] = "down"
        with mock.patch.object(prospect, "POLL_SECONDS", 0):
            code, err = self.main("scrape", self.proj, "--out", self.base / "raw.json")
        self.assertEqual(code, 2)
        self.assertEqual(err.strip(), "prospect: Docker is not running")
        self.assertEqual(self.opened.read_text(), "-a Docker")
        self.assertFalse(self.log.exists())
        self.assertFalse((self.base / "raw.json").exists())


class SourceTest(Base):
    def test_parse_accepts_array_and_json_lines(self):
        rows = [{"title": "A"}, {"title": "B"}]
        self.assertEqual(prospect.parse_results(json.dumps(rows)), rows)
        self.assertEqual(prospect.parse_results("\n".join(json.dumps(r) for r in rows) + "\n"), rows)
        self.assertEqual(prospect.parse_results(""), [])
        # v1.18.2 writes one JSON array per query, one per line
        self.assertEqual(prospect.parse_results('[{"title": "A"}]\n[]\n[{"title": "B"}]\n'), rows)
        self.assertEqual(prospect.parse_results(json.dumps(rows, indent=2)), rows)

    def test_geocode_empty_result_stops(self):
        self.write_profile(center="1 Nowhere Lane, Atlantis")
        with mock.patch.object(prospect, "urlopen") as op:
            op.return_value.__enter__.return_value.read.return_value = b"[]"
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = prospect.main(["plan", str(self.proj)])
        self.assertEqual(code, 2)
        self.assertEqual(err.getvalue().strip(), "prospect: could not geocode center")
        req = op.call_args[0][0]
        self.assertIn("q=1+Nowhere+Lane", req.full_url)
        self.assertEqual(req.get_header("User-agent"), "trevskills-prospect/1.0")
        with mock.patch.object(prospect, "urlopen") as op:
            op.return_value.__enter__.return_value.read.return_value = b'[{"lat": "47.62", "lon": "-122.35"}]'
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = prospect.main(["plan", str(self.proj)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["center"], [47.62, -122.35])


class SkillDocTest(unittest.TestCase):
    def test_skill_md_documents_every_profile_key(self):
        text = (HERE / "SKILL.md").read_text()
        self.assertEqual(list(prospect.PROFILE_KEYS), [
            "business", "targets", "exclude_categories", "exclude_chains", "center", "radius_miles",
            "conversion_pct", "avg_order_value", "goal_jobs", "min_rating", "max_results", "must_have_contact",
            "outreach", "site_url", "business_address", "voice_skill", "fast_mode"])
        for key in prospect.PROFILE_KEYS:
            self.assertIn(f"`{key}`", text, key)

    def step(self, text, start, end):
        return text[text.index(start):text.index(end)]

    def test_score_and_spot_check_treat_scraped_text_as_data(self):
        text = (HERE / "SKILL.md").read_text()
        spot = self.step(text, "4. **Spot-check", "5. **Filter.")
        score = self.step(text, "6. **Score.", "7. **Ingest.")
        for name, body in (("spot-check", spot), ("score", score)):
            self.assertIn("never instructions", body, name)
        for phrase in ("WebFetch only", "no Bash, Write or Edit"):
            self.assertIn(phrase, spot)

    def test_site_url_row_limits_http_to_localhost(self):
        line = next(x for x in (HERE / "SKILL.md").read_text().splitlines() if x.startswith("| `site_url`"))
        self.assertIn("localhost", line)
        self.assertIn("127.0.0.1", line)


if __name__ == "__main__":
    unittest.main()
