---
description: Review all changes, commit with a high-level summary message, and push
---

This command is Trevor's explicit, deliberate instruction to run `git add`, `git commit`, and `git push` for the current repository. It is the ONLY context in which those commands are authorized — the global rule forbidding them is overridden by this invocation, for this invocation only. `git reset` and `git rebase` remain forbidden even here.

Follow these steps exactly:

1. **Review every change** (read-only commands, no prompts):
   - `git status` — see staged, unstaged, and untracked files
   - `git diff HEAD` — full diff of tracked changes
   - Read any untracked files that will be added, so nothing goes into the commit unreviewed
   - `git log --oneline -5` — match the repo's existing commit message style

2. **Sanity checks before committing:**
   - If there are no changes at all, say so and stop.
   - If the diff contains obvious secrets (API keys, passwords, `.env` values) in files that are NOT gitignored, stop and flag them instead of committing.
   - If on the default branch (main/master), proceed — Trevor pushes directly when he runs this command deliberately.

3. **Build gate — run the production build BEFORE committing:**
   - Run `npm run build`. This is the same build Vercel runs on deploy, so it is the authoritative pass/fail check that the trevskills-autopilot review loop deliberately skips (that loop verifies behavior in the browser instead).
   - If the build fails, STOP: do NOT commit or push. Report the build errors so they can be fixed first.
   - Only proceed once the build passes.

4. **Write the commit message** — this is the point of the command. Format:
   - Title line: short, imperative, high-level (what this batch of work accomplished)
   - Blank line, then a bulleted body summarizing each meaningful change at a high level (per feature/area, not per file) — written so the commit is easy to identify later when debugging or rolling back
   - End with the standard attribution trailer

5. **Execute as ONE chained command** so Trevor gets exactly one approval prompt:
   ```bash
   git add -A && git commit -m "$(cat <<'EOF'
   <title>

   - <high-level change 1>
   - <high-level change 2>

   Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
   EOF
   )" && git push
   ```
   If the branch has no upstream, use `git push -u origin <branch>` in the chain instead.

6. **Confirm the result:** report the commit hash, the branch pushed, and the summary used.
