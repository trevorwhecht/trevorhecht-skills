# "/lead finder" from a video vs trevskills-prospect vs gosom

Date: 2026-11-25. Question: what does the "/lead finder" skill pitched in a short video do that
`trevskills-prospect` does not, is any of it worth copying, and should a universal version be built that anyone
can install?

## Sources

- **The video.** An Instagram reel (`https://www.instagram.com/reel/Dfpm8EmTjKx/`), read as a saved transcript of
  17 lines (896 bytes). It is a promotional pitch with no implementation detail. The skill itself is not public:
  the reel offers it to viewers who comment a keyword. Everything below about the video is the transcript's claim,
  not verified.
- **trevskills-prospect.** `global/skills/trevskills-prospect/SKILL.md` and `prospect.py` at `origin/main` `0d86761`.
- **gosom.** `gosom/google-maps-scraper`, the image `prospect.py` runs (`IMAGE = "gosom/google-maps-scraper:v1.18.2"`,
  `prospect.py:20`). Its README and its GitHub metadata (MIT license) were read on 2026-11-25. `prospect.py` reads
  its `title`, `category`, `address`, `web_site`, `phone`, `emails`, `review_rating` and `review_count` fields
  (`prospect.py:199-201`).
- **Platform terms**, read on 2026-11-25: `reddit.com/robots.txt`, `google.com/robots.txt`, the Google Maps
  additional terms (`google.com/help/terms_maps/`), the X terms (`x.com/en/tos`) and the LinkedIn User Agreement.
  The Meta and Instagram terms pages did not load for a script, so they are paraphrased, not quoted.

## What the video claims

1. Type `/lead finder`, paste your website, get "a full lead list".
2. Each lead's "pains, their dreams, their objections in their exact words".
3. "thousands of profiles at a time across every social platform".
4. "it sends the outreach for you, written off the exact words that those people used online".
5. Setup is one skill that makes four: "a scraper, a profile builder, an email finder, and a sender".

Not stated: which platforms, how it reads them, which email finder or sending service, cost, volume limits,
opt-out handling or platform terms.

## Capability table

| | Video (transcript only) | trevskills-prospect | gosom |
|---|---|---|---|
| lead source | "every social platform", "thousands of profiles at a time"; platforms and method not stated | Google Maps places inside a radius of one center point (through gosom), plus one pasted Facebook or Instagram post in `post` mode | Google Maps search and place pages: name, category, address, website, phone, emails, rating, review count and more |
| own-words pains/dreams/objections | Claimed for every lead, "in their exact words" | No. Each lead gets a one-line `reason` the model writes about the business (SKILL.md step 6); nothing the lead said is quoted | No. `-extra-reviews` collects reviews, but those are customers' words about the business, not the business's own needs |
| email finding | Claimed ("an email finder"); method not stated. Guessing name patterns or a paid lookup service are the usual ways (unverified) | Emails gosom found on the business's own website, junk and duplicates removed, own domain first (`clean_emails`, `prospect.py:353`); never guessed | `-email` reads the listed website and up to three same-site contact or about pages and extracts printed addresses |
| outreach drafting | Claimed: written "off the exact words" each lead used | Optional `draft` mode: a short email per lead that has an email, at most 30 per run (`MAX_DRAFTS`, `prospect.py:26`), address and opt-out appended; built from the scraped fields and fit reason, not from the lead's words | None |
| sending | Claimed: sends the outreach for you | Never sends: drafts land on the project's leads page for the owner to send | None |
| platform terms | Bulk reading of social profiles runs against the Meta, Instagram, LinkedIn and X terms and Reddit's robots.txt (below); every auto-sent cold email has to meet CAN-SPAM | Refuses to scrape Facebook or Instagram; email only, never SMS or calls (TCPA); inherits gosom's Google Maps position (next column) | Google's robots.txt allows `/maps/search/` and `/maps/place/`, but the Maps terms say not to "mass download or create bulk feeds of the content"; its README warns "Unauthorized scraping may violate terms of service." |
| cost | Not stated; the skill is a comment-for-access giveaway. Reading thousands of social profiles per run normally needs a paid scraping service or API (unverified) | Free to run: local Docker and gosom, local fit scoring; model tokens for the spot-check and drafts | Free and MIT licensed; runs locally (Docker or a binary) |
| setup | Unknown | Docker, a project repo with `prospect/profile.json`, and that project's `/api/leads/ingest` endpoint and token | Docker or the Go binary |

Platform terms, as read:
- Reddit `robots.txt`: `User-agent: *` / `Disallow: /`, pointing to its Public Content Policy.
- X terms: "crawling or scraping the Services in any form, for any purpose without our prior written consent is
  expressly prohibited".
- LinkedIn User Agreement: do not use "software, devices, scripts, robots or any other means or processes ... to
  scrape or copy the Services, including profiles and other data from the Services".
- Meta and Instagram terms (paraphrased): no collecting data from their products by automated means without
  their prior permission.
- CAN-SPAM (FTC guide): no misleading headers or subject lines, identify the message as an ad, include a valid
  physical postal address, give a way to opt out and honor it within 10 business days.

## Gaps worth copying

1. **The lead's own words.** Pains, dreams and objections as verbatim quotes, each with the URL where the lead
   wrote it. This is the one thing the video describes that neither `trevskills-prospect` nor gosom does. A quote
   can be checked by opening its URL; a model-written `reason` cannot.
2. **Leads from public conversation.** A Maps search finds businesses by category; it cannot find the person who
   just posted that their supplier let them down again. Public forum threads, Q&A sites, search snippets and
   public business pages can, without logging in anywhere.
3. **Emails with provenance.** Keep an email only when the lead's own page prints it, and record that page's URL.
   `trevskills-prospect` already does this for Maps rows through gosom; the new skill does it for every lead.
4. **Outreach drafted from those words.** A draft that refers to what the lead said and answers their objection,
   still written for a person to read and send.

## What not to copy

- **Auto-send.** Every commercial email has CAN-SPAM duties (address, opt-out, honest subject, ad disclosure), and
  cold email to people in Canada, the EU or the UK often needs prior consent (CASL, GDPR, PECR). A sender mailing
  unchecked addresses in bulk also burns the sending domain's reputation. A person reading each draft is the only
  check on a wrong lead or a misread quote. `trevskills-prospect` already drafts only; so does the new skill.
- **Scraping Facebook, Instagram, LinkedIn or X.** Their terms forbid automated collection (quoted above).
  `trevskills-prospect` already refuses Facebook and Instagram and takes one pasted post instead.
- **Bulk social scraping.** "Thousands of profiles at a time" is bulk collection of personal data, and it is not
  what makes the leads good: twenty leads with real quotes beat two thousand rows. The new skill reads at most 30
  pages per run.
- **Fetching Reddit pages.** Its robots.txt disallows every path for every agent. The new skill uses only what a
  search result shows, and names `trevskills-reddit-thread` (official API) for reading a thread in full.
- **Guessed emails.** Pattern guesses (`first.last` at a domain) or lookup services give addresses the person never
  published, and they bounce.
- **SMS and calls.** TCPA, as `trevskills-prospect` already says.

## Verdict
Partial
1. The lead's own words, quoted with a URL, are the one real gap: `trevskills-prospect` writes its own one-line
   reason for each lead and quotes nothing the lead said, and gosom collects no such text.
2. That half can ship as a markdown-only skill (`global/skills/trevskills-leads-finder/SKILL.md`) that runs on web
   search and page fetches alone: no Docker, project repo, site backend or API key, so anyone can install it.
3. The rest of the pitch is left out on purpose: auto-send, bulk scraping and the named social platforms conflict
   with CAN-SPAM, the platforms' own terms and Reddit's robots.txt, and the email finder is unspecified, so the
   skill drafts only and keeps an email only when the lead's own page prints it.
4. The video's skill could not be inspected (transcript only): it is handed out only to viewers who comment on the
   reel, and the 17-line transcript has no implementation detail, so its scale, platforms, email finder and sender
   are unverified claims.
5. `trevskills-prospect` stays as it is for Maps prospecting into a project's leads page; own-words quotes
   are now added to its `post` mode (job 118): verbatim, checked against the pasted text.
