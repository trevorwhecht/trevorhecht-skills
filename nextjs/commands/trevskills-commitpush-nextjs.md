---
description: Next.js variant of /trevskills-commitpush — same flow, with the Vercel build (npm run build) as a required gate
---

Follow `/trevskills-commitpush` exactly, every step and every rule, with only these overrides. If neither `/trevskills-commitpush` nor `/global:trevskills-commitpush` is in this session's command list, STOP and report that it is missing. Do not reconstruct it from memory.

## Overrides

- **Step 0.5 — skip it.** You are already in the tailored variant. Do not defer again, so the two commands never hand off to each other in a loop.
- **Step 3 — the build gate is `npm run build`.** This is the same build Vercel runs on deploy. It is not optional and it replaces the generic build-command search. If it fails, STOP: do not commit or push, and report the build errors.

Nothing else changes.
