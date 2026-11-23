# Prompt audit, 2026-11-22

Method: the `prompt-audit` workflow of the bundled `claude-api` skill (`shared/prompt-audit.md`), Steps 0-6.
Run against `origin/main` at `a041e77`. Every line number below is a line of `git show origin/main:<path>`.

## Step 0: scope, target model, what was applied

- **Scope.** The prompt surface is every `.md` file in the repository: everything under `global/`, `macos/`
  and `nextjs/`, plus the repo `CLAUDE.md` and `README.md`. That is 36 files, 250,037 bytes, listed with
  sizes in the Inventory below. `git ls-tree -r --name-only origin/main | grep '\.md$'` prints the same 36 paths.
- **Skipped, and why.**
  - Scripts (`global/skills/trevskills-mine/mine.py`, `global/skills/trevskills-prospect/prospect.py`,
    `global/skills/trevskills-reddit-thread/reddit_thread.py`, `global/skills/trevskills-transcript-mining/transcript_signals.py`,
    `macos/skills/trevskills-link-mac/setup_token.py`, `macos/skills/trevskills-owa-usage/owa_usage.py`,
    `global/skills/trevskills-skill-scan/scan.sh`, `macos/skills/trevskills-mac-cleanup/trevskills-mac-cleanup.sh`,
    `macos/skills/trevskills-mac-cleanup/deep-audit.sh`) and their `test_*.py` files: none sends text to a model.
    `git grep -nE 'claude -p|claude-(opus|sonnet|haiku)|anthropic' origin/main -- '*.py' '*.sh'` prints nothing, so
    they hold no request-building code. They were read only to check that the commands and flags the skills name
    still exist (Group 2, volatile specifics).
  - `.claude-plugin/marketplace.json` and the three `*/.claude-plugin/plugin.json` manifests: package metadata
    only, no prompt text.
  - `global/skills/trevskills-prospect/profile.example.json`, `.gitignore` and `LICENSE`: data, not prompt text.
  - User-level configuration (`~/.claude/` and the files skills point at there) is outside the project and was
    not audited. Where a skill names such a file, the path is reported, not probed.
- **Target model.** Claude Opus 5.5 / Claude Sonnet 5.5, the models that read these files in Claude Code.
  No in-scope file pins its own model: `git grep '^model:' origin/main` prints nothing.
- **Nothing was applied.** This report and `audits/prompt-audit-2026-11-22.diff` are proposals. No skill,
  command, rule, `CLAUDE.md` or `README.md` text was changed by the audit. Step 7 (behavioural probes) was not
  run, because no edit is applied.

## Summary

The highest-impact findings are stale facts the repository itself contradicts. The README's install steps say
`global/rules/` holds `scalable-template.md` and copy only `global/rules/*.md`, but that file moved to
`nextjs/rules/` in `f44ac3d` (#17), so a reader following the README never installs it (F1). The timecard skill
tells the model to "set `PAY_RATE` below", and no `PAY_RATE` exists anywhere in the repository (F4). The
Twilio skill tells the model to run `prisma migrate dev` and a raw production `migrate deploy`, which the
newer `/trevskills-migrate` command forbids by name (F8).

The second theme is pressure language and history narrative in `trevskills-mac-cleanup`, the oldest skill text
in the repo: all-caps headings and warnings (F10, F12, F13), and dated one-off incidents kept as standing rules
(F19, F20, F21), plus a requirement restated with pressure (F22). Most of the history-narrative lines also carry a personal name, so their fixes are
described in prose here and left out of the committed diff (see "Flag reasons" below).

| Group | Findings | Edit findings in the diff |
|---|---|---|
| Group 1, dated prompt text | 13 | 6 |
| Group 2, brittle skill and configuration files | 26 | 11 |
| Group 3, tool descriptions | not applicable | - |
| Group 4, request config and architecture | not applicable | - |

Group 3 is not applicable: the repository defines no tools. Its only routing text is frontmatter `description:`
lines, which are trigger text and stay (keep-list item 6). Group 4 is not applicable: Step 1 found no
request-building or prompt-assembly code and no subagent definition files.

By confidence: 8 High and 9 Medium findings carry an edit, one hunk each (17 hunks, F1-F17). F18-F39 are `flag`
items: 9 Medium (F18-F26) and 13 Low (F27-F39).

## Inventory (Step 1)

| Path | Bytes | Lines |
|---|---|---|
| `CLAUDE.md` | 507 | 8 |
| `README.md` | 8575 | 125 |
| `global/commands/trevskills-commitpush.md` | 11014 | 242 |
| `global/commands/trevskills-datafix.md` | 6028 | 87 |
| `global/commands/trevskills-migrate.md` | 27439 | 379 |
| `global/rules/performance.md` | 2134 | 41 |
| `global/skills/trevskills-backlog/SKILL.md` | 2603 | 60 |
| `global/skills/trevskills-mine/SKILL.md` | 6018 | 118 |
| `global/skills/trevskills-owa-feedback/SKILL.md` | 1795 | 41 |
| `global/skills/trevskills-owa-message-check/SKILL.md` | 7194 | 135 |
| `global/skills/trevskills-prospect/SKILL.md` | 8475 | 110 |
| `global/skills/trevskills-reddit-thread/SKILL.md` | 1712 | 39 |
| `global/skills/trevskills-screenprint/SKILL.md` | 4195 | 42 |
| `global/skills/trevskills-screenprint/reference.md` | 58713 | 811 |
| `global/skills/trevskills-skill-scan/SKILL.md` | 3672 | 55 |
| `global/skills/trevskills-todo-report/SKILL.md` | 2097 | 48 |
| `global/skills/trevskills-transcript-mining/SKILL.md` | 2496 | 55 |
| `macos/skills/trevskills-link-mac/SKILL.md` | 3818 | 28 |
| `macos/skills/trevskills-mac-cleanup/SKILL.md` | 21760 | 171 |
| `macos/skills/trevskills-owa-usage/SKILL.md` | 2057 | 29 |
| `macos/skills/trevskills-timecard/SKILL.md` | 2459 | 53 |
| `nextjs/commands/trevskills-commitpush-nextjs.md` | 834 | 12 |
| `nextjs/rules/dashboard-nav.md` | 1042 | 12 |
| `nextjs/rules/scalable-template.md` | 2283 | 39 |
| `nextjs/skills/trevskills-nextjs-ui/SKILL.md` | 6759 | 92 |
| `nextjs/skills/trevskills-nextjs-ui/references/accessibility.md` | 5884 | 83 |
| `nextjs/skills/trevskills-nextjs-ui/references/apple-hig.md` | 2232 | 19 |
| `nextjs/skills/trevskills-nextjs-ui/references/forms.md` | 2741 | 56 |
| `nextjs/skills/trevskills-nextjs-ui/references/heroui.md` | 3141 | 28 |
| `nextjs/skills/trevskills-nextjs-ui/references/links.md` | 2249 | 50 |
| `nextjs/skills/trevskills-nextjs-ui/references/mobile.md` | 5485 | 119 |
| `nextjs/skills/trevskills-nextjs-ui/references/modals.md` | 5309 | 108 |
| `nextjs/skills/trevskills-nextjs-ui/references/styling.md` | 5696 | 127 |
| `nextjs/skills/trevskills-nextjs-ui/references/tables.md` | 13239 | 260 |
| `nextjs/skills/trevskills-nextjs-ui/references/ux-laws.md` | 687 | 11 |
| `nextjs/skills/trevskills-twilio-email-setup/SKILL.md` | 7695 | 230 |

The kinds of file found: 4 custom commands, 3 rule files, 16 skills (16 `SKILL.md` plus 11 reference files under two
of them), the repo `CLAUDE.md` and the `README.md`. No subagent definitions, output styles, few-shot blocks sent through
an API, or memory files. The skills name several files outside the project (user-level rules, scripts, other
repositories); those are reported by path where a finding needs them and never read.

## Provenance (Step 2)

`git blame` on `origin/main` (59 commits) splits the surface into three eras:

- **Initial commit `ec98b54` (2026-10-13).** The README install and rules sections, `trevskills-mac-cleanup`,
  `trevskills-timecard`, `trevskills-todo-report`, `trevskills-backlog`, `trevskills-twilio-email-setup` and
  `global/rules/performance.md`. Most of the all-caps emphasis is from here (mac-cleanup:16, :134, :158,
  timecard:23, performance.md:10). These lines predate the current model generation and no later commit
  revisited them.
- **Reconcile commit `f44ac3d` (#17, 2026-11-10).** It moved `scalable-template.md` from `global/rules/` to
  `nextjs/rules/`, added `nextjs/rules/dashboard-nav.md`, and rewrote much of `trevskills-migrate.md`. The
  README rules section was not updated with it (F1). The `/trevskills-migrate` rule against `prisma migrate dev`
  (migrate.md:87, :194) is from here, newer than the Twilio skill's opposite instruction (F8).
- **Per-skill commits after 2026-10-24.** `trevskills-screenprint` grew by dated additions (reference.md §10,
  2026-10-24 to 2026-11-19); the 2026-11-03 "Ink facts" block (reference.md:763-773) supersedes two earlier
  lines that were never edited (F5, F6, F18). `trevskills-nextjs-ui` was split and modernised in `e4c8571` (#8,
  2026-10-27), which left the skeleton-loader caps in place (F14).

No line names the model it was written for. Idiom-dating found one superpowers-era idiom (F33) and no
`think step by step`, scratchpad, prefill or word-cap scaffolds.

## Line classification (Step 3)

Most of the surface is context only the author knows, and stays: the shop's equipment and ink practice in
`trevskills-screenprint`, each script's commands, flags and exit codes, table sizes and alignment rules in
`trevskills-nextjs-ui`, the safety gates in the three commands, and the reasons beside most prohibitions.
Every command and flag a skill names was checked against its script without running it: `mine.py`
(`rank`, `text`, `mark`, `archive`, `--exclude`, `--apply`), `prospect.py` (`plan`, `scrape`, `check`, `filter`,
`score`, `ingest`, `--set`, `--drop-fields`, `--dry-run`, check exit 3), `transcript_signals.py` (`--days`, `--top`,
`--no-jev`, `--projects-dir`, `--jev`, `--out`, exit 2), `owa_usage.py` (`week`, `report`, `install`, `count`,
`--owa-only`, `OWA_USAGE_OTHER`), `scan.sh` (`SS_VERSION`, `SS_COMMIT`, `--no-llm`) and
`trevskills-mac-cleanup.sh` / `deep-audit.sh` (every subcommand in the Quick reference, `--self-check`,
`NEVER_RESET_RE`, `RESET_PROCS`, `RESET_CPU_PCT`, `RESET_RSS_MB`, `UNUSED_DAYS`, `LARGE_MB`). All resolve. The
`trevskills-nextjs-ui` Index names 41 headings across ten reference files; all exist. The deletion candidates are
the lines below.

## Findings (Steps 4-5)

Each edit finding has exactly one hunk in `audits/prompt-audit-2026-11-22.diff`; the hunk header carries the
finding id after the second `@@` (for example `@@ -57,5 +57,5 @@ F2`), so hunks can be taken one at a time.

### High

#### F1. README rules section points at the old rules folder

- **Location:** `README.md:90-99`
- **Evidence** `README.md:90`:
  ```text
  `global/rules/` holds two files that shape how Claude writes code:
  ```
- **Evidence** `README.md:93`:
  ```text
  - **`scalable-template.md`** — component boundaries
  ```
- **Evidence** `README.md:99`:
  ```text
  cp global/rules/*.md ~/.claude/rules/
  ```
- **Pattern:** Group 2, volatile specifics (a named path that no longer resolves).
- **Why obsolete:** `scalable-template.md` lives at `nextjs/rules/scalable-template.md` since `f44ac3d` (#17);
  `global/rules/` holds only `performance.md`. The copy command installs one of the two rules it describes.
- **Confidence:** High (the repository contradicts it).
- **Action:** `rewrite` lines 90-99 to name both real paths and copy both files:
  `Two rule files shape how Claude writes code:`, the two bullets prefixed `global/rules/` and `nextjs/rules/`,
  and `cp global/rules/*.md nextjs/rules/scalable-template.md ~/.claude/rules/`. Line 105's file list stays
  correct. Hunk F1.

#### F2. README names a skill that does not exist

- **Location:** `README.md:59`
- **Evidence** `README.md:59`:
  ```text
  | **backlog** | Capture one-line ideas into the project's `BACKLOG.md`
  ```
- **Pattern:** Group 2, volatile specifics (a named skill that does not resolve).
- **Why obsolete:** the skill is `trevskills-backlog` (`global/skills/trevskills-backlog/SKILL.md:2`); every other
  row uses the full name.
- **Confidence:** High.
- **Action:** `rewrite` `**backlog**` to `**trevskills-backlog**`. Hunk F2.

#### F3. todo-report sends the model to a skill name that does not exist

- **Location:** `global/skills/trevskills-todo-report/SKILL.md:48`
- **Evidence** `global/skills/trevskills-todo-report/SKILL.md:48`:
  ```text
  see the `backlog` skill
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** the skill is named `trevskills-backlog` (`global/skills/trevskills-backlog/SKILL.md:2`); a model
  looking for a `backlog` skill finds none.
- **Confidence:** High.
- **Action:** `rewrite` to `see the `trevskills-backlog` skill`. Hunk F3.

#### F4. timecard points at a `PAY_RATE` setting that does not exist

- **Location:** `macos/skills/trevskills-timecard/SKILL.md:23`
- **Evidence** `macos/skills/trevskills-timecard/SKILL.md:23`:
  ```text
  set `PAY_RATE` below (default **$0.00/hr** — edit this line)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** there is no `PAY_RATE` below line 23 or anywhere in the repository (`grep -rn PAY_RATE` finds
  only this line), so "below" sends the model looking for a setting that is not there. The rate is this line.
- **Confidence:** High.
- **Action:** `rewrite` the sentence to `Pay rate for totals: **$0.00/hr** (edit this line to set yours).` It stays
  on line 23, so `README.md:117` ("Line 23 ... reads `$0.00/hr`") stays true. Hunk F4.

#### F5. screenprint reference keeps a superseded HSA definition

- **Location:** `global/skills/trevskills-screenprint/reference.md:712`
- **Evidence** `global/skills/trevskills-screenprint/reference.md:712`:
  ```text
  **HSA** (clear base, e.g. Matsui OW Stretch)
  ```
- **Evidence** `global/skills/trevskills-screenprint/reference.md:764`:
  ```text
  HSA is Matsui's water-based high-solid line, not OW Stretch.
  ```
- **Pattern:** Group 2, instruction files that contradict each other (here two passages of one file, which
  load together).
- **Why obsolete:** line 764 (blame 2026-11-03) says HSA is not OW Stretch; line 712 (blame 2026-10-26) says it is.
  Loaded together the model has to reconcile them; read at line 712 alone it learns the wrong fact.
- **Confidence:** High (the newer line is explicit and `git blame` orders them).
- **Action:** `rewrite` line 712 to `**HSA** (Matsui's water-based high-solid line)`. When taking this hunk, also
  take F6 and fix line 763 by hand (F18). Hunk F5.

#### F6. screenprint reference repeats the superseded "OW Stretch = HSA"

- **Location:** `global/skills/trevskills-screenprint/reference.md:725`
- **Evidence** `global/skills/trevskills-screenprint/reference.md:725`:
  ```text
  OW Stretch = HSA,
  ```
- **Pattern:** Group 2, instruction files that contradict each other.
- **Why obsolete:** same contradiction as F5, against line 764 (2026-11-03 vs 2026-10-27).
- **Confidence:** High.
- **Action:** `rewrite` `OW Stretch = HSA,` to `OW Stretch, HSA,` so the line lists both as separate lines of the
  brand. Hunk F6.

#### F7. forms.md names the kit by its old name

- **Location:** `nextjs/skills/trevskills-nextjs-ui/references/forms.md:23`
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/forms.md:23`:
  ```text
  (or `startContent` / `endContent` in NextUI)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** the skill's kits are HeroUI and shadcn/ui (`SKILL.md:10`), and `references/heroui.md:8` documents
  the same `startContent` / `endContent` props under HeroUI. NextUI appears nowhere else in the repository.
- **Confidence:** High.
- **Action:** `rewrite` `in NextUI)` to `in HeroUI)`. Hunk F7.

#### F8. Twilio skill runs Prisma migrations the migrate command forbids

- **Location:** `nextjs/skills/trevskills-twilio-email-setup/SKILL.md:183`, against `global/commands/trevskills-migrate.md:87`
  and `:194`
- **Evidence** `nextjs/skills/trevskills-twilio-email-setup/SKILL.md:183`:
  ```text
  After modifying schema: `npx prisma migrate dev --name <name>` (local)
  ```
- **Evidence** `global/commands/trevskills-migrate.md:87`:
  ```text
  **Do not use `prisma migrate dev --create-only`.**
  ```
- **Evidence** `global/commands/trevskills-migrate.md:194`:
  ```text
  **Do not use `prisma migrate dev`.**
  ```
- **Pattern:** Group 2, instruction files that contradict each other.
- **Why obsolete:** the Twilio line (blame `ec98b54`, 2026-10-13) tells the model to run `migrate dev` and a raw
  production `migrate deploy`; the newer migrate command (blame `f44ac3d`, 2026-11-10) forbids `migrate dev` and
  gates production behind dev checks. The rewrite makes the older file match the newer, safer one; it tightens
  a rule and loosens nothing.
- **Confidence:** High.
- **Action:** `rewrite` line 183 to ``After modifying the schema, run `/trevskills-migrate` (global plugin): it migrates
  dev first, then production, behind its safety checks.`` The `nextjs` plugin already depends on `global`
  (`README.md:74`). Hunk F8.

### Medium

#### F9. performance rule steers thinking depth in prose

- **Location:** `global/rules/performance.md:10`
- **Evidence** `global/rules/performance.md:10`:
  ```text
  Take extra time to find it rather than brute-forcing
  ```
- **Pattern:** Group 1b, prose that steers thinking depth ("think harder").
- **Why obsolete:** on Opus 5.5 thinking is always on and depth is set by `effort`; a standing "take extra time"
  in a rule that loads every session pushes over-deliberation on every task, including trivial ones. The real
  requirement, prefer the performant solution over brute force, stays.
- **Confidence:** Medium.
- **Action:** `rewrite` to `- Look for the optimal solution first, rather than brute-forcing something that works but
  performs poorly.` Once synced to the installed rules this affects every project. Hunk F9.

#### F10. mac-cleanup report heading shouts

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:16`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:16`:
  ```text
  ## ALWAYS end every session with the report (required)
  ```
- **Pattern:** Group 1a, pressure language.
- **Why obsolete:** current models follow a plainly stated requirement; caps plus "(required)" plus the restatements
  at lines 18 and 37 make the report read as more important than the safety rules around it.
- **Confidence:** Medium.
- **Action:** `rewrite` to `## End every session with the report`. Lines 18 and 37 are F22. Hunk F10.

#### F11. mac-cleanup encodes one machine's signed-app list as the malware rule

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:125`, against `:85`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:125`:
  ```text
  on this machine everything is validly signed
  ```
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:125`:
  ```text
  Any `>>> UNSIGNED/UNKNOWN` line is a real "investigate this" signal
  ```
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:85`:
  ```text
  Homebrew binaries and open-source DBs (Firebird, Postgres) are legitimately unsigned
  ```
- **Pattern:** Group 2, the recency trap and volatile specifics; the two lines also disagree.
- **Why obsolete:** a published skill runs on other Macs, where "everything is validly signed" is not true, and line
  85 of the same file says Homebrew and database binaries are legitimately unsigned. A model reading line 125
  alone treats a running Postgres as a malware signal.
- **Confidence:** Medium.
- **Action:** `rewrite` to ``- **Malware flag:** investigate any `>>> UNSIGNED/UNKNOWN` line after ruling out the
  legitimately unsigned tools named under Deep audit (Homebrew binaries, open-source databases); for a true scan,
  point to Objective-See KnockKnock or Malwarebytes.`` Hunk F11.

#### F12. mac-cleanup offload limitation in caps

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:134`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:134`:
  ```text
  **CRITICAL LIMITATION — offload is a two-step, Finder-finished operation on modern macOS:**
  ```
- **Pattern:** Group 1a, pressure language.
- **Why obsolete:** the paragraph under it carries the reason; the caps add no information and add to the file's
  anxious register (CRITICAL, NEVER, ALWAYS, DO NOT across the file).
- **Confidence:** Medium.
- **Action:** `rewrite` to `**Limitation: on modern macOS, offload is a two-step operation that Finder finishes:**`.
  Hunk F12.

#### F13. mac-cleanup contacts warning shouts and narrates an incident

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:158`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:158`:
  ```text
  **⚠️ DO NOT casually escalate past here.** Both of the following BURNED the user for ~1 hour and did NOT fix a genuinely-wedged sync:
  ```
- **Pattern:** Group 1a, pressure language (with a Group 2 history narrative in the second sentence).
- **Why obsolete:** the stop is real and stays; the caps and "BURNED" carry no more than a plain statement, and the
  incident is better as its present-tense fact (each step took about an hour and did not fix the sync).
- **Confidence:** Medium.
- **Action:** `rewrite` to `**Stop here unless the user agrees to go further.** Each step below cost about an hour
  without fixing a genuinely wedged sync:`. The prohibition is kept, at normal volume. Hunk F13.

#### F14. skeleton-loader rules in caps

- **Location:** `nextjs/skills/trevskills-nextjs-ui/references/accessibility.md:61-65`
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/accessibility.md:61`:
  ```text
  Spinners are ONLY for action-pending buttons.
  ```
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/accessibility.md:63`:
  ```text
  renders IMMEDIATELY and is NEVER skeletoned.
  ```
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/accessibility.md:65`:
  ```text
  covers ONLY the dynamic content area.
  ```
- **Pattern:** Group 1a, pressure language (four caps markers in five lines).
- **Why obsolete:** the rest of the reference states rules at normal volume; four caps words in one paragraph stop
  carrying information and make this one section read as weightier than its neighbours.
- **Confidence:** Medium.
- **Action:** `rewrite` the four words to lower case (`only`, `immediately`, `never`, `only`); nothing else changes.
  Hunk F14.

#### F15. mobile.md opens with a bold "must" and "not optional"

- **Location:** `nextjs/skills/trevskills-nextjs-ui/references/mobile.md:7`
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/mobile.md:7`:
  ```text
  Mobile is not optional — design for the smallest screen first.
  ```
- **Pattern:** Group 1a, pressure language.
- **Why obsolete:** the whole line is bold, says "must", and argues against an objection the model is not making;
  the concrete UB rules under it do the work. `SKILL.md:10` already says mobile-first.
- **Confidence:** Medium.
- **Action:** `rewrite` to `Every component works as well on mobile as on desktop; design for the smallest screen
  first.` Hunk F15.

#### F16. the `next/image` example omits a required prop

- **Location:** `nextjs/skills/trevskills-nextjs-ui/references/styling.md:126`
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/styling.md:126`:
  ```text
  <Image src={src} alt={alt} className="aspect-video w-full object-cover" />
  ```
- **Pattern:** Group 2, volatile specifics (an API claim), in a single gold example (Group 1c).
- **Why obsolete:** `next/image` needs `width` and `height`, or `fill`, unless the image is a static import; with
  `src={src}` this example throws at runtime. An example is the strongest signal in a prompt, so the model copies
  the broken shape.
- **Confidence:** Medium (documented in the Next.js `Image` docs; not checkable inside this repo).
- **Action:** `rewrite` to a `fill` image in a sized wrapper:
  `<div className="relative aspect-video w-full">` / `<Image src={src} alt={alt} fill sizes="100vw"
  className="object-cover" />` / `</div>`. Hunk F16.

#### F17. reddit-thread explains its rule with a dated incident

- **Location:** `global/skills/trevskills-reddit-thread/SKILL.md:13`
- **Evidence** `global/skills/trevskills-reddit-thread/SKILL.md:13`:
  ```text
  On 2026-11-17 Reddit refused curl, old.reddit, the `.json` endpoint, WebFetch and the Chrome extension, and the thread had to be pasted by hand.
  ```
- **Pattern:** Group 2, history narratives.
- **Why obsolete:** the reason (unauthenticated reads are refused, so use OAuth) is context and stays; the date and
  "had to be pasted by hand" are archaeology that reads as one day's outage.
- **Confidence:** Medium.
- **Action:** `rewrite` to present tense: `Reddit refuses unauthenticated reads (curl, old.reddit, the `.json`
  endpoint, WebFetch and the Chrome extension), so this skill uses the official OAuth API.`, keeping the
  last30days sentence with "that refused `.json` endpoint". Hunk F17.

### Flags (no hunk)

**Flag reasons.** F18-F24 match a documented row at Medium confidence, but each fix would put a line holding a
personal name into the committed diff, either as the removed line or as its only possible context line. This
repository is public and its added lines must carry no personal names, so these lines are left out of the diff
and their proposed edit is given in prose. F25 and F26 sit in the four command files the request keeps out of the
diff (`trevskills-migrate`, `trevskills-datafix`, `trevskills-commitpush`, `trevskills-commitpush-nextjs`). F27-F39 are
Low-confidence items; of those, F28, F29, F30 and F39 are also in a keep-list command file and F31 is a frontmatter
`description:`, so they would be flags at any confidence.

#### F18. note that "replaces" earlier lines (Medium, flag)

- **Location:** `global/skills/trevskills-screenprint/reference.md:763`
- **Evidence** `global/skills/trevskills-screenprint/reference.md:763`:
  ```text
  these replace the earlier "HSA = OW Stretch" lines above
  ```
- **Pattern:** Group 2, time-sensitive content (information that should live in one place), with Group 1d
  migration-relative phrasing.
- **Why obsolete:** the note patches two lines it never fixed (F5, F6). Once those hunks land it points at text that
  is gone.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: when taking F5 and F6, drop the parenthetical so line 763 reads `- **Ink facts**:`.
  The line holds a personal name.

#### F19. asset sweep decision dated in the step (Medium, flag)

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:26`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:26`:
  ```text
  (decided 2026-08-24 — he wants this automatic, no approval step)
  ```
- **Pattern:** Group 2, history narratives.
- **Why obsolete:** the rule's authority is the behaviour (apply the asset sweep without approval), which line 27 gives
  with its reason; the decision date adds nothing.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: remove the parenthetical. Line 27, the only trailing context, holds a personal name.

#### F20. a one-off audit result kept as a standing rule (Medium, flag)

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:32`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:32`:
  ```text
  Found 2026-10-28: ~2.5 GB of uninstalled-app leftovers, Discord/Postman/Zoom unused, Claude desktop's 11 GB VM (he uses only the terminal and Chrome).
  ```
- **Pattern:** Group 2, the recency trap.
- **Why obsolete:** one session's findings on one Mac, written into every future run; the next run may steer toward
  those apps.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: delete that sentence. Line 33, the only trailing context, holds a personal name.

#### F21. "no longer needs approval" (Medium, flag)

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:77`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:77`:
  ```text
  **`assets` no longer needs approval**
  ```
- **Pattern:** Group 1d, migration-relative phrasing, with a Group 2 history narrative (a dated attribution).
- **Why obsolete:** "no longer" is a diff against a rule the model never saw.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: `with one deliberate exception: **`assets` applies without approval**.` and drop
  the dated attribution. The line holds a personal name.

#### F22. the report requirement restated with pressure (Medium, flag)

- **Location:** `macos/skills/trevskills-mac-cleanup/SKILL.md:18`, `:37`
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:18`:
  ```text
  wants a **full report every single time this skill is used**
  ```
- **Evidence** `macos/skills/trevskills-mac-cleanup/SKILL.md:37`:
  ```text
  Never skip the report — it is the point of running the skill for
  ```
- **Pattern:** Group 1a, pressure language; Group 1c, repetition as reinforcement.
- **Why obsolete:** F10's heading already states the requirement; two more emphatic restatements add no information.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: line 18 becomes `Workflow:`; drop the last sentence of line 37. Both lines hold
  a personal name.

#### F23. link-mac rule carries a dated attribution (Medium, flag)

- **Location:** `macos/skills/trevskills-link-mac/SKILL.md:12`
- **Evidence** `macos/skills/trevskills-link-mac/SKILL.md:12`:
  ```text
  **Over ssh first.** Once `ssh <alias> true` works, do every step on that Mac over ssh from here, even when
  ```
- **Pattern:** Group 2, history narratives.
- **Why obsolete:** the line ends in a dated attribution; the rule stands without it.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: drop the trailing dated attribution and name the requester as "the user".
  The line holds a personal name.

#### F24. dashboard-nav rule opens with its origin date (Medium, flag)

- **Location:** `nextjs/rules/dashboard-nav.md:3`
- **Evidence** `nextjs/rules/dashboard-nav.md:3`:
  ```text
  2026-11-10: any page added to an admin (or employee) dashboard's side nav must also appear in
  ```
- **Pattern:** Group 2, history narratives.
- **Why obsolete:** the rule's authority is what it prescribes, not when it was said.
- **Confidence:** Medium.
- **Action:** `flag`. Proposed edit: start the line at `Any page added to an admin ...`. The line holds a personal name.

#### F25. commitpush pins a retired model name in its trailer (Medium, flag)

- **Location:** `global/commands/trevskills-commitpush.md:97`, `:124`
- **Evidence** `global/commands/trevskills-commitpush.md:97`:
  ```text
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```
- **Evidence** `global/commands/trevskills-commitpush.md:124`:
  ```text
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```
- **Pattern:** Group 2, history narratives (pinned model names).
- **Why obsolete:** the trailer names one model generation and degrades silently at each release; line 82 already says
  to append the harness's own trailer.
- **Confidence:** Medium.
- **Action:** `flag` (keep-list file). For the owner to decide: name the running model generically or drop the
  model from the standard trailer.

#### F26. migrate gate text written as a diff against an older process (Medium, flag)

- **Location:** `global/commands/trevskills-migrate.md:310-311`
- **Evidence** `global/commands/trevskills-migrate.md:310`:
  ```text
  Nothing prompts you any more, so nothing but this
  ```
- **Pattern:** Group 1d, migration-relative phrasing.
- **Why obsolete:** "any more" describes a previous approval flow the model never saw.
- **Confidence:** Medium.
- **Action:** `flag` (keep-list file; the line also holds a personal name).

#### F27. screenprint rules carry dated attributions (Low, flag)

- **Location:** `global/skills/trevskills-screenprint/SKILL.md:19`, `:39`
- **Evidence** `global/skills/trevskills-screenprint/SKILL.md:19`:
  ```text
  a manual job that needs one is flashed with a flash that takes no head (
  ```
- **Evidence** `global/skills/trevskills-screenprint/SKILL.md:39`:
  ```text
  a manual job that needs one is flashed with a flash that takes no head (
  ```
- **Pattern:** Group 2, history narratives.
- **Why obsolete:** in the rules table the attribution adds nothing. In `reference.md` the same attributions mark
  the shop's own answers, which line 9 of SKILL.md says win over published figures; there they are sourcing and stay.
- **Confidence:** Low.
- **Action:** `flag`.

#### F28. commitpush-nextjs shouts STOP (Low, flag)

- **Location:** `nextjs/commands/trevskills-commitpush-nextjs.md:5`
- **Evidence** `nextjs/commands/trevskills-commitpush-nextjs.md:5`:
  ```text
  STOP and report that it is missing. Do not reconstruct it from memory.
  ```
- **Pattern:** Group 1a, pressure language.
- **Why obsolete:** a plain "stop" carries the same instruction; the reason sits beside it.
- **Confidence:** Low.
- **Action:** `flag` (keep-list file).

#### F29. migrate hardcodes other repositories' Prisma versions (Low, flag)

- **Location:** `global/commands/trevskills-migrate.md:30-31`
- **Evidence** `global/commands/trevskills-migrate.md:30`:
  ```text
  If `prisma.config.ts` exists (boisepartyco, quoting-template — Prisma 6.19)
  ```
- **Evidence** `global/commands/trevskills-migrate.md:31`:
  ```text
  If it does not exist (**onewitharts** — Prisma 5.22)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** version pins of repositories outside this one, with no verification date; they cannot be checked
  from here and will drift.
- **Confidence:** Low.
- **Action:** `flag` (keep-list file).

#### F30. datafix hardcodes a script count in another repository (Low, flag)

- **Location:** `global/commands/trevskills-datafix.md:19`
- **Evidence** `global/commands/trevskills-datafix.md:19`:
  ```text
  (usually `scripts/<name>.ts`; onewitharts has ~28)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** a count in another repository that nothing re-checks.
- **Confidence:** Low.
- **Action:** `flag` (keep-list file).

#### F31. transcript-mining description repeats itself (Low, flag)

- **Location:** `global/skills/trevskills-transcript-mining/SKILL.md:3`
- **Evidence** `global/skills/trevskills-transcript-mining/SKILL.md:3`:
  ```text
  agents stuck before writing their .md (10+ turns, none writing a .md)
  ```
- **Pattern:** Group 2, trigger text that grows one phrase at a time.
- **Why obsolete:** the parenthetical restates the phrase before it; descriptions ride in every request.
- **Confidence:** Low.
- **Action:** `flag` (frontmatter `description:`, keep-list item 6).

#### F32. timecard "ALWAYS create" (Low, flag)

- **Location:** `macos/skills/trevskills-timecard/SKILL.md:23`
- **Evidence** `macos/skills/trevskills-timecard/SKILL.md:23`:
  ```text
  ALWAYS create the calendar event(s) for any new timestamps in the input
  ```
- **Pattern:** Group 1a, pressure language.
- **Why obsolete:** possibly not: the emphasis is scoped to one demonstrated gap (answering a totals question without
  logging) and carries its reason, which is the case 1a allows. It shares the line with F4, so it gets no hunk of
  its own.
- **Confidence:** Low.
- **Action:** `flag`.

#### F33. "Announce at start" idiom (Low, flag)

- **Location:** `global/skills/trevskills-screenprint/SKILL.md:12`
- **Evidence** `global/skills/trevskills-screenprint/SKILL.md:12`:
  ```text
  **Announce at start:** "Using trevskills-screenprint for the production rules."
  ```
- **Pattern:** Step 2 idiom-dating (a fixed announcement line from an older skill style).
- **Why obsolete:** no row documents it; Claude Code already shows which skill loaded.
- **Confidence:** Low.
- **Action:** `flag`.

#### F34. dryer facts in §10 disagree across dates (Low, flag)

- **Location:** `global/skills/trevskills-screenprint/reference.md:692-693`
- **Evidence** `global/skills/trevskills-screenprint/reference.md:692`:
  ```text
  Auto → BBC Little Buddy, plastisol only for now. BBC Aeolus planned.
  ```
- **Evidence** `global/skills/trevskills-screenprint/reference.md:693`:
  ```text
  Water based on the Little Buddy was too slow
  ```
- **Pattern:** Group 2, instruction files that contradict each other.
- **Why obsolete:** line 692 (2026-10-24) still lists a planned Aeolus; lines 693-695 (2026-11-19) say a forced-air dryer
  twice the size was bought. The text does not say whether that dryer is the Aeolus, so history cannot settle it.
- **Confidence:** Low.
- **Action:** `flag`. The shop owner says which dryer feeds the auto now.

#### F35. link-mac points at a memory file outside the project (Low, flag)

- **Location:** `macos/skills/trevskills-link-mac/SKILL.md:19`
- **Evidence** `macos/skills/trevskills-link-mac/SKILL.md:19`:
  ```text
  see `reference_chrome_profiles.md`
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** no such file is in the repository; it is a user-level note, so a public user of the skill has
  nothing to read. Not probed.
- **Confidence:** Low.
- **Action:** `flag`.

#### F36. UB-19 cited for two different rules (Low, flag)

- **Location:** `nextjs/skills/trevskills-nextjs-ui/references/heroui.md:15`, against `references/forms.md:55`
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/heroui.md:15`:
  ```text
  Never a native `<select>` (UB-19)
  ```
- **Evidence** `nextjs/skills/trevskills-nextjs-ui/references/forms.md:55`:
  ```text
  never `confirm()` (UB-19)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** may be fine (UB-19 may cover all native browser controls), but the UB file is outside the
  project, so it cannot be checked here.
- **Confidence:** Low.
- **Action:** `flag`.

#### F37. README "What's inside" omits shipped items (Low, flag)

- **Location:** `README.md:53-83`
- **Evidence** `README.md:53`:
  ```text
  ## What's inside
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** the tables leave out five shipped items: `trevskills-owa-feedback`, `trevskills-reddit-thread`,
  `trevskills-screenprint`, `trevskills-skill-scan` and `/trevskills-datafix`. An omission is not a contradiction.
- **Confidence:** Low.
- **Action:** `flag`.

#### F38. Twilio console warning in caps, unverifiable here (Low, flag)

- **Location:** `nextjs/skills/trevskills-twilio-email-setup/SKILL.md:14`
- **Evidence** `nextjs/skills/trevskills-twilio-email-setup/SKILL.md:14`:
  ```text
  Email lives in `1console.twilio.com` — NOT the legacy `console.twilio.com`
  ```
- **Pattern:** Group 1a, pressure language; Group 2, an external claim with no verification date.
- **Why obsolete:** the caps are mild and the reason follows; the console claim is about an outside service and may
  have moved.
- **Confidence:** Low.
- **Action:** `flag`.

#### F39. migrate checks for a Paperclip agent run (Low, flag)

- **Location:** `global/commands/trevskills-migrate.md:26`
- **Evidence** `global/commands/trevskills-migrate.md:26`:
  ```text
  In a Paperclip agent run (`$PAPERCLIP_AGENT_ID` is set)
  ```
- **Pattern:** Group 2, volatile specifics.
- **Why obsolete:** nothing else in the repository mentions Paperclip; it may be a retired integration.
- **Confidence:** Low.
- **Action:** `flag` (keep-list file).

## What stays (the keep list)

- **Trigger text.** No hunk touches a frontmatter `description:` or `name:` line (keep-list item 6).
- **Fragile scripts.** `trevskills-migrate.md`, `trevskills-datafix.md`, `trevskills-commitpush.md` and
  `trevskills-commitpush-nextjs.md` get no hunk; their exact step order, STOP gates and forbidden-command lists are
  the low-freedom text keep-list item 3 protects. Findings in them are flags (F25, F26, F28, F29, F30, F39).
- **Safety prohibitions.** mac-cleanup's password rule (line 75) and never-kill denylist (line 120), skill-scan's
  read-only and static-only rules, prospect's "email only, never SMS or calls (TCPA)", owa-message-check's "never
  sends" and its token handling, and the reddit skill's "official API only" all carry reasons and encode real
  constraints (keep-list items 1 and 5). F13 lowers the volume of one warning and keeps its prohibition.
- **Named-defaults style list.** `styling.md`'s Slop ban list names specific looks to avoid; Group 1e keeps that form
  for frontend direction on Opus 5.5.
- **Source labels in reference.md.** The dated attributions in `trevskills-screenprint/reference.md` mark the shop's
  own answers, which the skill says override published figures (SKILL.md:9-10). They are sourcing, not cruft.
- **Working redundancy.** Restatements that agree stay (keep-list item 8): the Kruzer flash rule in screenprint
  SKILL.md:19 and :39, mine's "never propose scrum or SKILL.md edits" at lines 44-45 and 116-117, and
  owa-message-check's "all three sources" at lines 9 and 11.
- **Ordered steps.** `trevskills-mine` ("Never skip to step 5 early", line 16) and `trevskills-prospect` keep numbered
  steps because order matters there (the marker and the scrape-check-filter chain).
- **Format-pinning examples.** The TSX and table examples in `trevskills-nextjs-ui` pin exact class strings and stay
  (keep-list item 7); F16 corrects one, it does not remove it.

## Proposed diff (Step 6)

`audits/prompt-audit-2026-11-22.diff` holds 17 hunks, one per High or Medium edit finding (F1-F17), against
`origin/main`. `git apply --check` passes for the whole patch and for each hunk on its own. Each hunk header ends with
its finding id. Installed copies under `~/.claude` change only after a merge syncs them; F9 edits a rule that loads in
every session. Taking F5 or F6 leaves line 763 of `reference.md` pointing at text that is gone until F18's prose edit
is made by hand.
