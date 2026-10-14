---
name: trevskills-backlog
description: Use when noting a feature idea or task for later development, or reading back what's captured — "add that to the backlog", "note it for later", "backlog this", "what's on the backlog", or /trevskills-backlog. Captures one-line items in the project's BACKLOG.md. Works in any repo, any language.
allowed-tools: Read, Write, Edit, Glob, Bash(ls *)
---

# Backlog

Capture an idea for later, or show what's already captured. One backlog file per repo.

## Backlog or TODO[n]?

Two different tools. Pick by whether the code exists yet.

| Situation | Where it goes |
|---|---|
| A feature, page, or refactor that hasn't been started — no code to point at | **BACKLOG.md** (this skill) |
| A specific line or file that needs revisiting later | **`// TODO[n]:`** comment in that file, read back with `/trevskills-todo-report` |

If you're tempted to add a `TODO` to a file you aren't otherwise editing, it belongs in the backlog instead.

## Locating the file

1. Look for an existing `docs/superpowers/plans/BACKLOG.md`, then `docs/BACKLOG.md`. Use whichever exists.
2. If neither exists, create it at `docs/superpowers/plans/BACKLOG.md` when `docs/superpowers/plans/` is already there, otherwise at `docs/BACKLOG.md`.

Never create a second backlog in a repo that already has one.

New-file template:

```markdown
# Backlog

> Quick braindump of features to build later. Not fully specced — one line each.
> When ready, pull an item out, brainstorm/spec it properly, then build. Group related items if it makes sense.

## Ideas

```

## Adding an item

Append under `## Ideas`, one line, this shape:

```markdown
- [ ] **Short title** — what it is and why, one sentence.
```

- If the user gave no detail, write the line from the surrounding conversation rather than asking.
- Link any related plan, spec, or sibling backlog item inline: `Related: [add-deposit-amount-field.md](add-deposit-amount-field.md)`.
- **One line, always.** Do not expand an item into a spec, break it into subtasks, or add acceptance criteria — the whole point is a cheap braindump. Speccing happens later, when it's pulled out.
- Adding to the backlog is not a commitment to build it now. Never start implementing an item you were just asked to record.

## Listing

Print the unchecked items in file order, then any checked ones under a "Shipped" heading. Give the total count. If the file doesn't exist, say the repo has no backlog yet rather than creating one.

## When an item ships

Mark it `- [x]` instead of deleting it, so the file doubles as a record of what got built.
