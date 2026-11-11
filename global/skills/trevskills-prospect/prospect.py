#!/usr/bin/env python3
"""Deterministic half of /trevskills-prospect: profile, scrape, field check, filter, ingest.

  prospect.py plan   <project> [--set k=v ...]
  prospect.py scrape <project> --out raw.json [--set ...]
  prospect.py check  <raw.json> --project <project> [--set ...]
  prospect.py filter <raw.json> --project <project> [--drop-fields a,b] --out candidates.json [--set ...]
  prospect.py ingest <project> --candidates candidates.json --scores scores.json [--dry-run] [--set ...]

Every failure is one line `prospect: <what is wrong>` on stderr. Stdlib only.
"""
import argparse, json, math, os, re, subprocess, sys, tempfile, time
from fractions import Fraction
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

IMAGE = "gosom/google-maps-scraper:v1.18.2"
MAX_BATCH = 200
MAX_DRAFTS = 30
OPT_OUT = "If you'd rather not hear from me, just reply and I won't email again."
POLL_SECONDS, POLL_TRIES = 2, 60  # docker start wait: 60 polls x 2 s = 120 s
USER_AGENT = "trevskills-prospect/1.0"
CONTACT_FIELDS = {"phone": "phone", "email": "emails", "website": "website"}
FILL_FIELDS = ("id", "title", "category", "address", "website", "phone", "emails", "rating", "review_count",
               "open_hours", "latitude", "longitude")
WEEKDAYS = re.compile(r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", re.I)
LATLON = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")

# key -> default; REQUIRED marks keys with no default. Order is the order SKILL.md documents them.
REQUIRED = object()
PROFILE_KEYS = {
    "business": REQUIRED, "targets": REQUIRED, "exclude_categories": [], "exclude_chains": [],
    "center": REQUIRED, "radius_miles": REQUIRED, "conversion_pct": REQUIRED, "avg_order_value": REQUIRED,
    "goal_jobs": REQUIRED, "min_rating": 0, "max_results": REQUIRED,
    "must_have_contact": ["phone", "email", "website"], "outreach": REQUIRED, "site_url": REQUIRED,
    "business_address": None, "voice_skill": None, "fast_mode": True,
}


class Fail(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ---------- profile ----------

def project_dir(arg):
    if os.sep in arg or arg.startswith((".", "~")):
        return Path(arg).expanduser()
    return Path.home() / "Developer" / "repos" / arg


def parse_sets(pairs):
    out = {}
    for pair in pairs or []:
        key, eq, raw = pair.partition("=")
        if not eq or not key:
            raise Fail(f"--set needs key=value, got {pair!r}")
        if key not in PROFILE_KEYS:
            raise Fail(f"unknown key {key}")
        try:
            out[key] = json.loads(raw)
        except ValueError:
            out[key] = raw
    return out


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_str_list(v):
    return isinstance(v, list) and all(isinstance(x, str) and x.strip() for x in v)


def validate(p):
    for key in p:
        if key not in PROFILE_KEYS:
            raise Fail(f"unknown key {key}")
    for key, default in PROFILE_KEYS.items():
        if key not in p:
            if default is REQUIRED:
                raise Fail(f"profile is missing {key}")
            p[key] = list(default) if isinstance(default, list) else default

    def need(ok, key, what):
        if not ok:
            raise Fail(f"{key} must be {what}")

    need(isinstance(p["business"], str) and p["business"].strip(), "business", "a non-empty string")
    t = p["targets"]
    need(isinstance(t, list) and t and all(
        isinstance(x, dict) and set(x) <= {"category", "keywords"} and isinstance(x.get("category"), str)
        and x["category"].strip() and is_str_list(x.get("keywords")) and x["keywords"] for x in t),
        "targets", 'a non-empty list of {"category": string, "keywords": [string, ...]}')
    for key in ("exclude_categories", "exclude_chains"):
        need(is_str_list(p[key]), key, "a list of strings")
    c = p["center"]
    need(isinstance(c, str) and c.strip(), "center", '"lat,lon" or a street address')
    m = LATLON.match(c)
    if m:
        need(abs(float(m[1])) <= 90 and abs(float(m[2])) <= 180, "center", "a valid lat,lon")
    need(is_num(p["radius_miles"]) and p["radius_miles"] > 0, "radius_miles", "a number > 0")
    need(is_num(p["conversion_pct"]) and 0 < p["conversion_pct"] <= 100, "conversion_pct", "a number > 0 and <= 100")
    need(is_num(p["avg_order_value"]) and p["avg_order_value"] > 0, "avg_order_value", "a number > 0")
    need(type(p["goal_jobs"]) is int and p["goal_jobs"] >= 1, "goal_jobs", "an integer >= 1")
    need(is_num(p["min_rating"]) and 0 <= p["min_rating"] <= 5, "min_rating", "a number from 0 to 5")
    need(type(p["max_results"]) is int and 1 <= p["max_results"] <= 500, "max_results", "an integer from 1 to 500")
    mh = p["must_have_contact"]
    need(isinstance(mh, list) and mh and all(x in CONTACT_FIELDS for x in mh), "must_have_contact",
         "a non-empty list drawn from phone, email, website")
    need(p["outreach"] in ("find", "draft"), "outreach", "find or draft")
    u = p["site_url"]
    need(isinstance(u, str) and urlparse(u).scheme in ("http", "https") and urlparse(u).netloc, "site_url",
         "an http or https URL")
    a = p["business_address"]
    need(a is None or (isinstance(a, str) and a.strip()), "business_address", "a non-empty string")
    need(p["outreach"] != "draft" or a, "business_address", "set when outreach is draft")
    v = p["voice_skill"]
    need(v is None or (isinstance(v, str) and v.strip()), "voice_skill", "a non-empty string")
    need(isinstance(p["fast_mode"], bool), "fast_mode", "true or false")
    return p


def load_profile(project, sets):
    proj = project_dir(project)
    path = proj / "prospect" / "profile.json"
    overrides = parse_sets(sets)
    try:
        p = json.loads(path.read_text())
    except FileNotFoundError:
        raise Fail(f"no profile at {path}")
    except ValueError as e:
        raise Fail(f"{path} is not valid JSON ({e})")
    if not isinstance(p, dict):
        raise Fail(f"{path} must hold a JSON object")
    p.update(overrides)
    return proj, validate(p)


def center_of(p):
    m = LATLON.match(p["center"])
    if m:
        return [float(m[1]), float(m[2])]
    url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {"q": p["center"], "format": "jsonv2", "limit": 1})
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=20) as r:
            hits = json.loads(r.read())
        return [float(hits[0]["lat"]), float(hits[0]["lon"])]
    except (IndexError, KeyError, TypeError, ValueError):
        raise Fail("could not geocode center")
    except (URLError, OSError) as e:
        raise Fail(f"could not geocode center ({e})")


def queries(p):
    seen, out = set(), []
    for t in p["targets"]:
        for k in t["keywords"]:
            k = k.strip()
            if k.lower() not in seen:
                seen.add(k.lower())
                out.append(k)
    return out


def leads_needed(p):
    return math.ceil(Fraction(p["goal_jobs"]) * 100 / Fraction(str(p["conversion_pct"])))


def ev(p, fit):
    return p["conversion_pct"] / 100 * p["avg_order_value"] * fit / 100


# ---------- source ----------

# Script field -> scraper JSON keys, first non-empty wins. Fix here when the scraper renames a key.
SOURCE_KEYS = {
    "id": ("place_id", "data_id", "cid"), "title": ("title",), "category": ("category",),
    "address": ("address",), "website": ("web_site", "website"), "phone": ("phone",), "emails": ("emails",),
    "rating": ("review_rating", "rating"), "review_count": ("review_count", "reviews_count"),
    "open_hours": ("open_hours",), "latitude": ("latitude",), "longitude": ("longtitude", "longitude"),
    "status": ("status",),
}


def parse_results(text):
    text = text.strip()
    if not text:
        return []
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def docker_up():
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def ensure_docker():
    if docker_up():
        return
    subprocess.run(["open", "-a", "Docker"], capture_output=True)
    for _ in range(POLL_TRIES):
        time.sleep(POLL_SECONDS)
        if docker_up():
            return
    raise Fail("Docker is not running")


# TODO[3]: paid-source-swap — Outscraper and the Google Places API (New) are the later replacements for this
# free scraper (cleaner fields, no Docker); swap the body of fetch_places and keep its return shape.
def fetch_places(profile: dict, out_path: Path) -> list[dict]:
    """Run the pinned scraper in Docker around the profile center; return rows in the script's field names."""
    lat, lon = center_of(profile)
    ensure_docker()
    with tempfile.TemporaryDirectory(prefix="prospect-") as work:
        Path(work, "queries.txt").write_text("\n".join(queries(profile)))
        cmd = ["docker", "run", "--rm", "-v", f"{work}:/work", IMAGE, "-input", "/work/queries.txt",
               "-results", "/work/results.json", "-json", "-email", "-geo", f"{lat},{lon}",
               "-radius", str(round(profile["radius_miles"] * 1609.344)), "-exit-on-inactivity", "3m"]
        if profile["fast_mode"]:
            cmd.append("-fast-mode")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stderr.strip().splitlines() or ["no output"])[-1]
            raise Fail(f"scraper exited {r.returncode}: {tail}", 1)
        res = Path(work, "results.json")
        raw = parse_results(res.read_text()) if res.exists() else []
    return [{k: next((s[x] for x in keys if s.get(x) not in (None, "", [])), None) for k, keys in SOURCE_KEYS.items()}
            for s in raw]


# ---------- field check ----------

def phone_e164(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    digits = re.sub(r"\D", "", raw)
    if raw.strip().startswith("+"):
        return "+" + digits if 8 <= len(digits) <= 15 else None
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits[0] == "1":
        return "+" + digits
    return None


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(h))


def filled(v):
    return v not in (None, "", [], {})


def coords(r):
    lat, lon = r.get("latitude"), r.get("longitude")
    return (lat, lon) if is_num(lat) and is_num(lon) else None


def check_rows(rows, p, center):
    n = len(rows)
    fill = {f: round(sum(filled(r.get(f)) for r in rows) / n, 4) if n else 0.0 for f in FILL_FIELDS}
    tripped = []

    def trip(field, why):
        tripped.append({"field": field, "why": why})

    if n >= 5 and all(not r.get("rating") for r in rows):
        trip("rating", f"every one of {n} ratings is 0 or missing")
    if n >= 5 and all(not r.get("review_count") for r in rows):
        trip("review_count", f"every one of {n} review counts is 0 or missing")
    days = [frozenset(d.lower() for d in WEEKDAYS.findall(json.dumps(r["open_hours"])))
            for r in rows if filled(r.get("open_hours"))]
    if days and all(len(d) == 1 for d in days) and len(set(days)) == 1:
        trip("open_hours", f"all {len(days)} rows with hours list only {next(iter(days[0]))}")
    phones = [r["phone"] for r in rows if filled(r.get("phone"))]
    bad = sum(phone_e164(x) is None for x in phones)
    if phones and bad / len(phones) > 0.2:
        trip("phone", f"{bad} of {len(phones)} phones are not valid E.164")
    limit = p["radius_miles"] * 1.05
    far = sum(miles(center, c) > limit for c in map(coords, rows) if c)
    if far:
        trip("distance", f"{far} rows lie beyond {limit:g} miles")
    for f in ("website", "phone", "emails"):
        if n >= 5 and fill[f] == 0:
            trip(f, f"no row has a {f}")
    hit = {t["field"] for t in tripped}
    wholesale = n == 0 or fill["id"] < 0.5 or fill["title"] < 0.5 or {"website", "phone", "emails"} <= hit
    return {"rows": n, "fill": fill, "tripped": tripped, "wholesale": wholesale}


def load_rows(path):
    try:
        rows = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Fail(f"cannot read {path} ({e})")
    if isinstance(rows, dict):
        rows = rows.get("rows")
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise Fail(f"{path} must hold a list of row objects")
    return rows


# ---------- filter ----------

def filter_rows(rows, p, center, drop):
    seen, kept, dropped = set(), [], {}

    def out(reason):
        dropped[reason] = dropped.get(reason, 0) + 1

    cats = [c.lower() for c in p["exclude_categories"]]
    chains = [c.lower() for c in p["exclude_chains"]]
    for src in rows:
        r = {k: v for k, v in src.items() if k not in drop}
        rid = src.get("id")
        if not rid:
            out("no id")
            continue
        if rid in seen:
            out("duplicate")
            continue
        seen.add(rid)
        if "closed" in str(src.get("status") or "").lower():
            out("closed")
            continue
        if any(c in str(src.get("category") or "").lower() for c in cats):
            out("excluded category")
            continue
        if any(c in str(src.get("title") or "").lower() for c in chains):
            out("chain")
            continue
        c = coords(src)
        if c:
            dist = miles(center, c)
            if dist > p["radius_miles"]:
                out("outside radius")
                continue
            r["distance_mi"] = round(dist, 2)
        if "rating" not in drop and is_num(src.get("rating")) and src["rating"] < p["min_rating"]:
            out("below min rating")
            continue
        if "phone" in r:
            r["phone"] = phone_e164(r["phone"]) or ""
        if not any(filled(r.get(CONTACT_FIELDS[k])) for k in p["must_have_contact"]):
            out("no contact")
            continue
        kept.append(r)
    kept.sort(key=lambda r: r.get("distance_mi", math.inf))
    if len(kept) > p["max_results"]:
        dropped["over max results"] = len(kept) - p["max_results"]
        kept = kept[:p["max_results"]]
    return kept, dropped


# ---------- ingest ----------

def read_token(proj):
    tok = os.environ.get("LEADS_AGENT_TOKEN", "").strip()
    if tok:
        return tok
    try:
        for line in (proj / ".env.local").read_text().splitlines():
            key, eq, val = line.strip().removeprefix("export ").partition("=")
            if eq and key.strip() == "LEADS_AGENT_TOKEN":
                tok = val.strip().strip("'\"")
    except OSError:
        pass
    if not tok:
        raise Fail("LEADS_AGENT_TOKEN is not set")
    return tok


def load_scores(path):
    try:
        scores = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise Fail(f"cannot read {path} ({e})")
    ok = isinstance(scores, list) and all(
        isinstance(s, dict) and isinstance(s.get("id"), str) and is_num(s.get("fit")) and 0 <= s["fit"] <= 100
        and isinstance(s.get("reason"), str) and isinstance(s.get("draft", ""), str) for s in scores)
    if not ok:
        raise Fail(f'{path} must be a list of {{"id", "fit" 0-100, "reason", "draft"?}}')
    return {s["id"]: s for s in scores}


def build_lead(row, score):
    emails = row.get("emails") or []
    email = emails[0] if isinstance(emails, list) and emails else emails if isinstance(emails, str) else None
    lead = {"source": "prospect", "placeId": row["id"], "name": row.get("title"), "company": row.get("title"),
            "email": email, "phone": phone_e164(row.get("phone")), "website": row.get("website"),
            "address": row.get("address"), "category": row.get("category"), "distanceMi": row.get("distance_mi"),
            "rating": row.get("rating"), "reviewCount": row.get("review_count"), "summary": score["reason"],
            "conversionProbability": round(score["fit"])}
    return {k: v for k, v in lead.items() if filled(v)}


def post(url, token, leads):
    req = Request(url, data=json.dumps({"leads": leads}).encode(), method="POST",
                  headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urlopen(req, timeout=60) as r:
            r.read()
    except HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise Fail(f"ingest failed: HTTP {e.code} {' '.join(body.split())}".replace(token, "[token]"), 1)
    except (URLError, OSError) as e:
        raise Fail(f"ingest failed: {e}".replace(token, "[token]"), 1)


def ingest(proj, p, cand_path, score_path, dry_run):
    raw = json.loads(Path(cand_path).read_text()) if Path(cand_path).exists() else None
    rows = load_rows(cand_path)
    meta = raw if isinstance(raw, dict) else {}
    scores = load_scores(score_path)
    dropped = dict(meta.get("dropped") or {})
    ranked = []
    for r in rows:
        s = scores.get(r.get("id"))
        if s is None:
            dropped["unscored"] = dropped.get("unscored", 0) + 1
            continue
        ranked.append((ev(p, s["fit"]), r, s))
    ranked.sort(key=lambda x: (-x[0], x[1].get("distance_mi", math.inf)))
    drafting = p["outreach"] == "draft"
    leads, drafts = [], 0
    for _, r, s in ranked:
        lead = build_lead(r, s)
        if drafting and drafts < MAX_DRAFTS and "email" in lead and (s.get("draft") or "").strip():
            lead["draftMessage"] = f"{s['draft'].rstrip()}\n\n{p['business_address']}\n{OPT_OUT}"
            drafts += 1
        leads.append(lead)
    if dry_run:
        for i, ((value, r, s), lead) in enumerate(zip(ranked, leads), 1):
            dist = f"{lead['distanceMi']} mi" if "distanceMi" in lead else "? mi"
            contact = lead.get("email") or lead.get("phone") or lead.get("website") or "-"
            print(f"{i}. fit {lead['conversionProbability']}  ev ${value:.0f}  {lead.get('name', '?')}  {dist}  "
                  f"{contact}  — {s['reason']}")
    else:
        token = read_token(proj)
        url = p["site_url"].rstrip("/") + "/api/leads/ingest"
        for i in range(0, len(leads), MAX_BATCH):
            post(url, token, leads[i:i + MAX_BATCH])
    found = meta.get("found", len(rows))
    why = ", ".join(f"{k} {v}" for k, v in dropped.items()) or "none"
    done = f"would ingest {len(leads)}" if dry_run else f"ingested {len(leads)}"
    print(f"found {found} · dropped: {why} · {done} · drafts {drafts} · "
          f"leads to goal {max(0, leads_needed(p) - len(leads))}")


# ---------- cli ----------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="prospect.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sets = argparse.ArgumentParser(add_help=False)
    sets.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    sub.add_parser("plan", parents=[sets]).add_argument("project")
    sc = sub.add_parser("scrape", parents=[sets])
    sc.add_argument("project")
    sc.add_argument("--out", required=True)
    ck = sub.add_parser("check", parents=[sets])
    ck.add_argument("raw")
    ck.add_argument("--project", required=True)
    fl = sub.add_parser("filter", parents=[sets])
    fl.add_argument("raw")
    fl.add_argument("--project", required=True)
    fl.add_argument("--drop-fields", default="")
    fl.add_argument("--out", required=True)
    ig = sub.add_parser("ingest", parents=[sets])
    ig.add_argument("project")
    ig.add_argument("--candidates", required=True)
    ig.add_argument("--scores", required=True)
    ig.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        proj, p = load_profile(a.project, a.set)
        if a.cmd == "plan":
            print(json.dumps({"center": center_of(p), "radius_m": round(p["radius_miles"] * 1609.344),
                              "queries": queries(p), "leads_needed": leads_needed(p),
                              "ev_per_lead_at_fit_100": round(ev(p, 100), 2)}, indent=2))
        elif a.cmd == "scrape":
            rows = fetch_places(p, Path(a.out))
            Path(a.out).write_text(json.dumps(rows, indent=1))
            print(f"scraped {len(rows)} rows into {a.out}")
        elif a.cmd == "check":
            rep = check_rows(load_rows(a.raw), p, center_of(p))
            print(json.dumps(rep, indent=2))
            return 3 if rep["wholesale"] else 1 if rep["tripped"] else 0
        elif a.cmd == "filter":
            rows = load_rows(a.raw)
            center = center_of(p)
            rep = check_rows(rows, p, center)
            if rep["wholesale"]:
                bad = ", ".join(t["field"] for t in rep["tripped"]) or "no usable rows"
                raise Fail(f"field check failed wholesale ({rep['rows']} rows; {bad}), nothing written", 3)
            drop = {f.strip() for f in a.drop_fields.split(",") if f.strip()}
            kept, dropped = filter_rows(rows, p, center, drop)
            Path(a.out).write_text(json.dumps({"found": len(rows), "dropped": dropped, "rows": kept}, indent=1))
            print(json.dumps({"found": len(rows), "kept": len(kept), "dropped": dropped}))
        else:
            ingest(proj, p, a.candidates, a.scores, a.dry_run)
    except Fail as e:
        print(f"prospect: {e}", file=sys.stderr)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
