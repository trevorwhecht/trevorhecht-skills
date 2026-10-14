---
name: trevskills-autopilot
description: Use when the user wants something built end-to-end in one shot — a feature, fix, component, or skill — and does not want to manually run each superpowers step or approve between phases. Triggers on "/trevskills-autopilot", "just build it", "run the whole thing", "do it all autonomously", "don't stop for approval".
---

# Autopilot

## Overview

Runs the full superpowers development chain from a single invocation: clarify → spec → plan → execute → review → report. No manual skill hand-offs, no approval stops after clarify. Orchestrates the EXISTING superpowers skills for their content — this skill only strips their approval-gate, git, and separate-session machinery.


## When to Use

- User says `/trevskills-autopilot <what to build>`, "just build it", "run the whole thing", "do it all".
- Any time the goal is a finished, reviewed change without babysitting each step.

**When NOT to use:**
- User wants to explore/collaborate on the design → use superpowers:brainstorming instead.
- User only wants a plan, or only a review → invoke that single skill directly.

## Two Hard Rules (do not negotiate)

**1. NEVER run git.** No `add`, `commit`, `push`, `branch`, `worktree`, `reset`, `rebase` — at any phase. Write spec/plan docs to disk and leave them unstaged. The user owns all git.

**2. NEVER stop for approval once phase 1 (Spec) begins.** Run straight through to the report. Do NOT pause because the tree is uncommitted, because a phase "seems big", or to confirm — the user runs git afterward and expects a finished result.

## Red Flags — you are about to violate this skill

- Reaching for `git add`/`git commit`/`git checkout -b` → STOP. The user handles git.
- "I'll just check in with the user before executing" → STOP. No stops after clarify.
- "The review found a lot, I'll report instead of fixing" → STOP. Auto-fix and loop (up to 3 rounds).
- "This is big, I should ask first" → STOP. Ask only in phase 0, only if essential.
- Opening Playwright to "verify it works" → STOP. Track B is opt-in only (see Phase 4). Types + tests + code review are the default.
- Pointing Playwright at :3001 or "localhost" without checking the port → STOP. :3001 is the PRODUCTION DB. Only :3000.
- Running `next build` to verify → STOP. Build lives in `/trevskills-commitpush`, not the review loop.

## The Phase Flow

Create one todo per phase and run them in order.

### Phase 0 — Clarify (stingy)
Ask ONLY questions whose wrong answer would waste real work. Prefer **zero** questions. If the request is unambiguous, ask nothing and proceed. Run FULL superpowers:brainstorming **only if** the user's invocation explicitly says "brainstorm".

### Phase 1 — Spec
Produce a concise design doc using superpowers:brainstorming's spec format. Save to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Run its spec self-review (placeholder scan, consistency, scope, ambiguity) and fix inline. **Do not commit.** From here on, no stops.

### Phase 1.5 — Logic docs (ALWAYS, before planning any change to existing behaviour)

`ls docs/logic/` and read `docs/logic/README.md`'s index. If a file there covers the logic this
change touches, **read it before writing the plan.** It is the source of truth for rules that span
several files, and reading it is far cheaper — and far more reliable — than re-deriving them by
grepping.

- The plan states which logic docs it read and which it will update.
- Any doc whose rules the change alters is updated **in phase 3, in the same run** — never "later".
  A stale logic doc is worse than none, because the next run will trust it.
- If the change establishes cross-file rules no doc covers yet, create one, applying the
  "When to add a file here" test in the README. Do not create one for a rule a single well-named
  function already states.
- No `docs/logic/` in this repo? Skip it. Do not scaffold the folder for a change that does not
  need it.

### Phase 2 — Plan
**REQUIRED SUB-SKILL:** use superpowers:writing-plans for the plan's structure. Save to `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`. **Do not commit.**

### Phase 3 — Execute
**REQUIRED SUB-SKILL:** use superpowers:subagent-driven-development to implement the plan in the current session and current branch. Each task follows superpowers:test-driven-development. Edits land directly in the working tree.

### Phase 4 — Review + auto-fix loop (NO build)

**Track A — Static code review (ALWAYS runs).** Dispatch a superpowers:requesting-code-review subagent (logic, security, conventions).

**Default verification (ALWAYS runs):** `npx tsc --noEmit` + `npx jest` + reading the changed code. That is the whole verification step unless Track B is explicitly triggered.

**Track B — Live browser walkthrough (Playwright MCP) — OFF BY DEFAULT.**

Browser automation is the most expensive thing in a session: every snapshot, screenshot, and DOM dump burns a large share of the token budget. It is NOT a routine verification step. Do not reach for it to "confirm it works."

Run Track B **only** when one of these is true:
- The user explicitly asks for it ("test it in the browser", "drive the app", "verify in the UI").
- Static reading has already failed to explain a bug that only reproduces through the live UI.
- The deliverable is purely visual/interactive AND the user asked for visual confirmation.

If Track B does not run, say so in the report — list what was verified (types/tests/review) and what was left for the user to click through. That is an expected outcome, not a gap to paper over.

When Track B DOES run:
- **⚠️ DB SAFETY — non-negotiable.** Only ever drive **http://localhost:3000** (plain `next dev` → dev DB). NEVER **:3001** (`dev:prod` → the **PRODUCTION** database) or any deployed/staging URL. Before any action that could write data, confirm the target is :3000. If only :3001 is up, do NOT test against it — start :3000 (`npm run dev`) or stop and tell the user.
- **Auth.** Log in at `/` using `TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD` from `.env.local` (a dev-DB Employee row with `isAdmin=true`; auth is NextAuth CredentialsProvider). If those env vars are missing, report the one-time setup step and skip Track B rather than guessing credentials.
- **Budget it.** Fewest steps that prove the thing. Targeted selectors over full-page snapshots; one screenshot at the end, not one per step. Never re-snapshot to "check" what a screenshot already showed.
- **Scope.** Only the feature just built. Not adjacent flows, not the whole site.
- **Evidence, not vibes.** Report what you drove and what you observed.

**Loop:**
1. Track A (plus Track B if it ran) clean? → exit.
2. Otherwise dispatch subagent(s) to fix findings at root cause (superpowers:receiving-code-review for how to weigh feedback), then re-run the tracks that ran.
3. **Cap: 3 rounds.** After the cap, stop looping.

No `next build` in this loop — the full build runs once at `/trevskills-commitpush` (the deploy gate). Never silently drop findings; anything unresolved at the cap goes in the report.

**Data-vs-code check before calling anything "broken":** the local dev DB and production hold different datasets. A count that looks wrong ("should be 178, I see 13") is a data difference until proven otherwise — check the raw API/DB response before hunting for a filter bug.

### Phase 5 — Report
Summarize: what was built, files created/modified, test status, review status, and any findings left unresolved at the 3-round cap. Then STOP. No git.

## Quick Reference

| Phase | Sub-skill borrowed | Stripped |
|---|---|---|
| 0 Clarify | brainstorming | one-at-a-time interrogation (unless user says "brainstorm") |
| 1 Spec | brainstorming (spec + self-review) | user-review gate, git commit |
| 1.5 Logic docs | — | (new) read `docs/logic/` before planning; update in the same run |
| 2 Plan | writing-plans | git commit, separate-session handoff |
| 3 Execute | subagent-driven-development + test-driven-development | — |
| 4 Review | requesting-code-review + tsc/jest (Playwright only on explicit request) | `next build` (moved to `/trevskills-commitpush`), routine browser driving |

## Common Mistakes

- **Planning a change to existing logic without reading `docs/logic/`.** Those files exist so you load one page instead of re-deriving a cross-file rule by grepping — and so you find out the rule has a reason before "simplifying" it away.
- **Changing behaviour a logic doc describes and leaving the doc stale.** The doc change ships with the code change, same run. Next run will trust whatever is written there.
- **Committing the spec/plan docs.** They are written but must stay unstaged.
- **Asking clarifying questions mid-run.** Questions are phase-0 only.
- **Stopping after review to let the user fix.** Auto-fix and re-review up to 3 rounds first.
- **Full brainstorming by default.** Only when the user explicitly asks to brainstorm.
- **Driving the browser by default.** Playwright is opt-in (Phase 4, Track B). It is the biggest token cost in a session.
- **Testing against :3001 (prod DB) or a deployed URL.** Only ever :3000.
- **Running `next build` in the review loop.** The build is the `/trevskills-commitpush` gate now.
