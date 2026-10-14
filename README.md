# trevorhecht-skills

Claude Code skills and commands I use daily, packaged as three installable plugins.

Opinionated by design — these encode how *I* work (npm, TypeScript, Tailwind + shadcn, Prisma, Next.js App Router). Fork and edit freely.

---

## Install

### Quickest — as plugins

```
/plugin marketplace add trevorwhecht/trevorhecht-skills
```

Then install whichever you want:

```
/plugin install global@trevorhecht-skills
/plugin install nextjs@trevorhecht-skills
/plugin install macos@trevorhecht-skills
```

That's it. Skills become available immediately, and update later with `/plugin marketplace update trevorhecht-skills`.

> **Naming note:** installed as a plugin, skills are namespaced — `trevskills-nextjs-ui` becomes `/nextjs:trevskills-nextjs-ui`, `trevskills-autopilot` becomes `/global:trevskills-autopilot`. If you'd rather type the bare names, use the manual install below.

### Manual — copy into `~/.claude`

Keeps the original unnamespaced names (`/trevskills-nextjs-ui`, `/trevskills-autopilot`):

```bash
git clone https://github.com/trevorwhecht/trevorhecht-skills.git
cd trevorhecht-skills

# skills (flatten all three categories into one folder)
mkdir -p ~/.claude/skills
cp -R global/skills/*  ~/.claude/skills/
cp -R nextjs/skills/*  ~/.claude/skills/
cp -R macos/skills/*   ~/.claude/skills/

# slash commands
mkdir -p ~/.claude/commands
cp global/commands/*.md ~/.claude/commands/
```

Restart Claude Code afterward.

---

## What's inside

### `global` — stack-agnostic

| | |
|---|---|
| **trevskills-autopilot** | Runs a full build end-to-end from one invocation: clarify → spec → plan → execute → review → report, with no approval stops in between. **Requires superpowers** ([setup below](#superpowers-setup)). |
| **backlog** | Capture one-line ideas into the project's `BACKLOG.md` and read them back. Works in any repo, any language. |
| **trevskills-todo-report** | Scans the codebase for `TODO[priority]` comments and returns them ranked 1–10. Pairs with the TODO format in `rules/performance.md`. |
| **/trevskills-commitpush** | Reviews every change, runs the production build as a gate, writes a high-level summary commit message, then commits and pushes in one chained command. |
| **/trevskills-migrate** | A Prisma migration behind real safety checks: duplicate-column detection, a best-practices pass, SQL generated and reviewed before it's applied, a data-loss scan with live row counts, an auto-generated rollback script, then dev → gate → production. |

### `nextjs`

| | |
|---|---|
| **trevskills-nextjs-ui** | Component selection, modal patterns, styling rules, layout, tables, accessibility, and mobile responsiveness for Next.js + shadcn/ui + Tailwind. The largest skill here. |
| **trevskills-twilio-email-setup** | Twilio email/SMS wiring for Next.js: env vars, domain authentication, correct request shapes, and the common 400 errors with their causes. |

### `macos`

| | |
|---|---|
| **trevskills-mac-cleanup** | Disk space, bloated "System Data", sluggishness, runaway processes, Adobe junk, iCloud offloading, adware persistence checks. Ships two shell scripts. **Deletes files — read the warning below.** |
| **trevskills-timecard** | Turns pasted "Time in" / "Time out" timestamps into Apple Calendar events for a work shift. |

---

## Superpowers setup

**Only `trevskills-autopilot` requires this.** It orchestrates superpowers' own skills (`writing-plans`, `subagent-driven-development`, `test-driven-development`, and both code-review skills) rather than reimplementing them — without superpowers installed, trevskills-autopilot has nothing to call.

Superpowers ships in the official marketplace that comes with Claude Code, so there's no marketplace to add:

```
/plugin install superpowers@claude-plugins-official
```

Verify it took by checking that `superpowers:brainstorming` appears in your skill list, then restart Claude Code.

`backlog` *mentions* a `docs/superpowers/plans/` path but doesn't need the plugin — it falls back to `docs/BACKLOG.md` when that folder doesn't exist. Every other skill here is standalone.

---

## Rules (manual step)

`global/rules/` holds two files that shape how Claude writes code:

- **`performance.md`** — speed, cost, and data-efficiency requirements, plus the `TODO[priority]` format that `trevskills-todo-report` scans for.
- **`scalable-template.md`** — component boundaries, framework isolation, CSS-variable theming, `src/` structure.

Plugins can't auto-install rules, so copy them yourself and reference them from your own `CLAUDE.md`:

```bash
mkdir -p ~/.claude/rules
cp global/rules/*.md ~/.claude/rules/
```

Then add to `~/.claude/CLAUDE.md`:

```markdown
*Rules in `~/.claude/rules/` (performance.md, scalable-template.md) auto-load with this file.*
```

---

## Before you use these

Read this section first — several of these skills take real action.

- **`trevskills-mac-cleanup` deletes files.** It empties cache directories and can thin Time Machine local snapshots via `sudo`. Destructive steps are gated behind an `APPLY` flag, but read `trevskills-mac-cleanup.sh` before running it with that flag set.
- **`/trevskills-commitpush` commits and pushes without asking.** By design — invoking it *is* the confirmation. It will push to your current branch, including a default branch.
- **`/trevskills-migrate` writes to your production database.** It runs dev first, then a go/no-go gate, then production in the same pass. It takes a `pg_dump` backup and refuses to continue if any check fails, but understand the flow before running it. Destructive Prisma flags and database resets are refused at every step.
- **`trevskills-timecard` has a placeholder pay rate.** Line 23 of `macos/skills/trevskills-timecard/SKILL.md` reads `$0.00/hr` — set it to yours or totals come out as zero.
- **`trevskills-autopilot` doesn't stop for approval.** That's the whole point of it. Don't reach for it on work you want to review phase by phase.

My own setup also hard-blocks database resets and history-rewriting git commands through a `PreToolUse` hook. That hook isn't included here — these skills assume you've made your own call about guardrails.

---

## License

MIT — see [LICENSE](LICENSE). Use them, fork them, change them. No attribution needed.
