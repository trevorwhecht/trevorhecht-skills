---
name: trevskills-todo-report
description: Scan the codebase for all TODO comments and return them ranked by priority 1–10. Use when the user asks for a TODO report, wants to see what's outstanding, or runs /trevskills-todo-report.
disable-model-invocation: true
allowed-tools: Bash(grep *)
---

## TODO scan results

```!
grep -rn "TODO" . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.py" --include="*.css" --include="*.md" --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git --exclude-dir=dist --exclude-dir=build --exclude-dir=venv --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=worktrees 2>/dev/null | head -200 || echo "No TODOs found"
```

## Instructions

Parse the grep output above and split it into two buckets:

- **Structured** — matches `TODO[n]:` where `n` is 1–10
- **Unformatted** — any other `TODO` mention

For each structured TODO capture the priority, the file path and line number, and the full text. TODOs often span several comment lines — read the file to pick up the continuation lines rather than reporting only the first.

### Output

Rank highest priority first, grouped into three tiers. Omit a tier that has no entries.

- 🔴 **Critical (8–10)** — must fix soon
- 🟡 **Medium (4–7)** — finish when there's time
- 🟢 **Low (1–3)** — nice to have, cool ideas

Format each entry as:

**[priority]/10 — [file path]:[line number]**
[full TODO description]

### Summary

Close with the total count and the count per tier.

Then list any **unformatted TODOs** separately, so they can be rewritten in the standard `TODO[n]:` shape. Skip this section when there are none. Ignore matches that are documentation *about* the TODO convention itself rather than actual outstanding work.

If the grep hit the 200-line cap, say so explicitly — do not present a truncated list as complete.

If nothing was found, say "No TODOs found in this project."

## Related

Ideas with no code yet belong in the project's `BACKLOG.md` — see the `backlog` skill — not in a `TODO[n]` comment.
