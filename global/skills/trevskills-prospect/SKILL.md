---
name: trevskills-prospect
description: Find nearby businesses likely to buy from a project's business (screen printing, event rentals, other trades), check the scraped fields, score and rank them, optionally draft outreach emails, and post them to the project's leads page. Scrapes Google Maps locally and free with Docker. Use for /trevskills-prospect <project> [overrides], or /trevskills-prospect <project> post <pasted text or url>.
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(mkdir *), Read, Write, Grep, Glob, Agent
---

# Local lead prospecting

`prospect.py` (next to this file, stdlib Python) does every deterministic step. You do the judgement:
the spot-check, the fit scores, the drafts, the pasted-post mode and the report. Run on demand only.

`<project>` is a repo path, or a bare name resolved as `~/Developer/repos/<name>`. Overrides are
`key=value` pairs; pass each one as `--set key=value` to **every** `prospect.py` call of the run, so the
scrape, the check and the filter all see the same radius and center. Work in a fresh
`W=$(mktemp -d)`.

## Profile: `<project>/prospect/profile.json`

All keys snake_case. A missing file, missing required key, wrong type, out-of-range value or unknown key
stops `prospect.py` with one `prospect: ...` line; show that line and stop. `profile.example.json` here is a
working example.

| Key | Required | Meaning |
|---|---|---|
| `business` | yes | What the business sells, in a sentence. Scoring reads it. |
| `targets` | yes | Non-empty list of `{"category": string, "keywords": [string, ...]}`. Each keyword is one Maps search. |
| `exclude_categories` | no, `[]` | Maps categories to drop (case-insensitive substring), e.g. competitors. |
| `exclude_chains` | no, `[]` | Business names to drop (case-insensitive substring of the title). |
| `center` | yes | `"lat,lon"`, or a street address geocoded once per call through Nominatim. |
| `radius_miles` | yes | Number > 0. Search and keep radius. |
| `conversion_pct` | yes | Expected % of leads that become a job, > 0 and ≤ 100. |
| `avg_order_value` | yes | Average job value, > 0. |
| `goal_jobs` | yes | Jobs wanted, integer ≥ 1. `leads_needed = ceil(goal_jobs / (conversion_pct / 100))`. |
| `min_rating` | no, `0` | Drop rows whose Maps rating is below this (0 to 5). |
| `max_results` | yes | Keep at most this many nearest rows per run (1 to 500). |
| `must_have_contact` | no, all three | Non-empty list from `phone`, `email`, `website`; a row needs at least one of them. |
| `outreach` | yes | `find` (leads only) or `draft` (leads plus email drafts). |
| `site_url` | yes | http(s) base URL of the project site; leads go to `<site_url>/api/leads/ingest`. |
| `business_address` | when `draft` | Sender's physical address, appended to every draft (CAN-SPAM). |
| `voice_skill` | no | Name of an installed skill that holds the sender's voice. |
| `fast_mode` | no, `true` | Scraper fast mode (strict radius). Set `false` when fast mode returns too little. |

Expected value per lead = `conversion_pct / 100 × avg_order_value × fit / 100`; leads are ranked by it.

## Run order

`S=~/.claude/skills/trevskills-prospect/prospect.py`

1. **Plan.** `python3 $S plan <project> [--set ...]`. Show the center, radius, queries and leads needed.
2. **Scrape.** `python3 $S scrape <project> --out $W/raw.json [--set ...]`. It starts Docker Desktop when it is
   quit and waits up to 2 minutes; `prospect: Docker is not running` means stop and say so. Runs take a few
   minutes (the scraper exits after 3 minutes with no new results).
3. **Check.** `python3 $S check $W/raw.json --project <project> [--set ...]`. Exit 0: go on. Exit 3
   (`wholesale`): stop, ingest nothing, and report the check. Exit 1: spot-check.
4. **Spot-check (exit 1 only).** Spawn one Agent with `model: "haiku"`. Give it the `tripped` list and 3 rows
   from `raw.json` that have a website; it opens each business's own website and compares rating, review
   count, hours, phone, email and address, and returns only the names of the fields that are broken (from the
   row's field names). Those names go to `--drop-fields`. A broken field is dropped, never sent wrong.
5. **Filter.** `python3 $S filter $W/raw.json --project <project> --out $W/candidates.json
   [--drop-fields a,b] [--set ...]`. It drops closed places, excluded categories, chains, rows outside the
   radius, rows below `min_rating`, rows with no contact and duplicates, and prints the counts.
6. **Score.** Read `candidates.json` (`rows`) and the profile. For every row, write a fit of 0 to 100 (how
   likely this business is to buy from `business`, given its category, name, size and distance) and a
   one-line reason; the reason becomes the lead's summary. Write `$W/scores.json`:
   `[{"id": "<row id>", "fit": 72, "reason": "Runs three youth leagues; orders jerseys each season"}]`. A row
   you leave out is dropped as `unscored`. In `draft` mode, add a `draft` to rows with an email (see Outreach).
7. **Ingest.** `python3 $S ingest <project> --candidates $W/candidates.json --scores $W/scores.json
   [--set ...]`. Add `--dry-run` when asked for one: it prints the ranked leads and posts nothing. The token
   is `LEADS_AGENT_TOKEN` from the environment or `<project>/.env.local`; never print it. A non-2xx response
   stops the run; show its line.
8. **Report.** Quote the script's last line (found, dropped by reason, ingested or would ingest, drafts, leads
   to goal), the fields dropped after the spot-check, and any new `prospect/voice.md`.

## Outreach

Email only: never SMS or calls (TCPA), and nothing is sent by the skill. Drafts land on the lead as
`draftMessage`; the owner reviews and sends them. In `find` mode drafts are ignored. In `draft` mode the
script keeps drafts only on leads with an email, at most 30 per run (the highest ranked), and appends the
`business_address` and a one-line opt-out to each, so write the draft without a signature block address or
opt-out. Keep it short: who you are, why this business, one concrete offer, one question.

**Voice.** Professional (neutral, polished) unless `<project>/prospect/voice.md` exists (follow it) or the
profile names a `voice_skill` (read that skill and follow its voice rules). Once the project's mailbox, read
through the Gmail MCP, holds at least 10 sent prospect emails that got a reply, build
`<project>/prospect/voice.md` from those exact emails (tone, openings, length, sign-off, quoted examples),
and name the new file in the report so it gets committed.

## Facebook and Instagram

Never scrape Facebook or Instagram, logged in or not. Instead:

`/trevskills-prospect <project> post <pasted text or url>` turns one pasted post into one lead (plus a draft
reply in `draft` mode) through the same `ingest`:
- Only a URL was pasted: ask for the post text, then go on.
- Write the pasted text or url, exactly as pasted, to `$W/post.txt` and take its id from
  `python3 -c 'import hashlib,sys;print("post:"+hashlib.sha1(open(sys.argv[1],"rb").read()).hexdigest()[:12])' $W/post.txt`.
- Write `$W/candidates.json` as `{"found": 1, "rows": [{"id": "<post id>", "title": "<poster or group
  name>", "category": "Facebook post", "website": "<post url>", "phone": "...", "emails": ["..."]}]}` with
  only the fields the post gives, then score it and run step 7.
- A post with no URL, email or phone cannot be ingested: say so in one line and stop.
