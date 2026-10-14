---
description: Performance, cost, and TODO tracking rules — applies to all projects
---

## Performance & Cost Philosophy

Every project should be as lightweight, fast, and cheap to run as possible. These are design requirements, not afterthoughts.

**Speed & load time:**
- Always look for the optimal solution first. Take extra time to find it rather than brute-forcing something that works but performs poorly.
- If a brute-force approach is the only immediate option, implement it but always leave a structured TODO comment so it gets cleaned up later.

**TODO format:**
```
// TODO[priority]: Brief title — detailed description of what needs attention, why it was
// left incomplete, and ideally what the ideal solution looks like.
```
- `priority` is 1–10 (10 = must fix soon, 1 = nice to have)
- Run `/trevskills-todo-report` at any time for a ranked list across the project

**Flexible TODO input:**

| You say | I do |
|---|---|
| Priority + description | Format and write it exactly |
| Description only | Infer priority from context |
| Priority only | Write description from current conversation |
| Just "leave a TODO" | Write both from context |

**Data & storage efficiency:**
- Only fetch and store what is actually needed — no over-fetching, no SELECT *
- Design schemas to avoid redundant data storage from the start
- Prefer nullable fields and soft deletes over storing duplicate state

**Cost awareness:**
- Current target: ~$20/month (Vercel + Prisma, same accounts across projects)
- Upgrades are acceptable if genuinely required by scale — not acceptable if caused by a fixable design decision
- Flag any design choice that will meaningfully increase infrastructure costs before implementing
- If a cheaper architectural option exists that doesn't sacrifice meaningful quality, always prefer it
