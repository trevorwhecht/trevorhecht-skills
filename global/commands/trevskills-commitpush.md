---
description: Review all changes, commit with a high-level summary message, and push
---

This command is the explicit, deliberate instruction to run `git add`, `git commit`, and `git push` for the current repository. It is the ONLY context in which those commands are authorized — the global rule forbidding them is overridden by this invocation, for this invocation only. `git reset` and `git rebase` remain forbidden even here.

**This command never merges anything.** Not `gh pr merge`, not `git merge`, not a push to `main`/`master` from any other branch, not auto-merge. The repo owner is the only one who merges, and they do it by clicking **Squash and merge** in the GitHub UI. This is permanent. If you reach the end of this command and the work is not merged, that is the command working correctly.

## Step 0 — Pick the path

```bash
git rev-parse --abbrev-ref HEAD
```

- Branch is `main` or `master` → **Path A (solo)**. Steps 1–4, then 5A, then 6.
- Branch is anything else → **Path B (agent branch)**. Steps 1–4, then 5B, then 6.
- Output is `HEAD` (detached) → STOP. Report the detached HEAD and do not commit.
- Branch is not `main`/`master` but IS this repo's default branch (check `git symbolic-ref refs/remotes/origin/HEAD`) → STOP and report. Do not guess which path applies.

Steps 1 through 4 are identical on both paths.

## Step 0.5 — Defer to a tailored variant

Some stacks have a tailored version of this command that overrides parts of it. Check before Step 1:

| Variant | Repo matches when | Command names |
| --- | --- | --- |
| Next.js | `package.json` lists `next` in `dependencies` or `devDependencies` | `/trevskills-commitpush-nextjs`, `/nextjs:trevskills-commitpush-nextjs` |

- Repo matches a variant AND either of its command names appears in this session's command list → follow that command instead, from its start. Stop reading this one.
- Repo matches but neither name is in the command list → continue here. Step 3 below picks the build gate.
- Repo matches no variant → continue here.

Decide availability from the session's command list only. Do not go looking in `~/.claude`.

---

## Step 1 — Review every change

Read-only commands, no prompts:

- `git status` — see staged, unstaged, and untracked files
- `git diff HEAD` — full diff of tracked changes
- Read any untracked files that will be added, so nothing goes into the commit unreviewed
- `git log --oneline -5` — match the repo's existing commit message style

## Step 2 — Sanity checks before committing

- If there are no changes at all, say so and stop.
- If the diff contains obvious secrets (API keys, passwords, `.env` values) in files that are NOT gitignored, stop and flag them instead of committing. Name the file path — never paste the secret itself into a report, comment, or issue.
- If on the default branch (main/master), proceed — the repo owner pushes directly when they run this command deliberately. (That is Path A.)

## Step 3 — Build gate: run the repo's own build BEFORE committing

Pick the build command from the repo root. Go down this list and use the **first** match only:

1. **`scrum/project.md` names one.** It has a `Build:` line whose value is not `none` → run that value exactly.
2. **`package.json` has a `build` script.** Run it with the package manager the lockfile names:
   - `pnpm-lock.yaml` → `pnpm run build`
   - `yarn.lock` → `yarn build`
   - `bun.lockb` or `bun.lock` → `bun run build`
   - none of those → `npm run build`
3. **An obvious native build exists.**
   - `Makefile` with a `build` target → `make build`
   - `Cargo.toml` → `cargo build`
   - `go.mod` → `go build ./...`
   - `pyproject.toml` with a `[build-system]` table → `python -m build`
4. **Nothing matched.** There is no build gate. Do not invent one, and do not fall back to `npm run build`. Skip to Step 4, and put this line in the Step 6 report: **"No build gate: this repo has no build command."**

A `Build: none` line in `scrum/project.md` does not stop the search — go on to 2 and 3.

If the build fails, STOP: do NOT commit or push. Report the build errors so they can be fixed first. Only proceed once the build passes.

The trevskills-autopilot review loop deliberately skips the build (it verifies behavior in the browser instead), so this gate is the authoritative pass/fail check.

## Step 4 — Write the commit message

This is the point of the command. Format:

- Title line: short, imperative, high-level (what this batch of work accomplished)
- Blank line, then a bulleted body summarizing each meaningful change at a high level (per feature/area, not per file) — written so the commit is easy to identify later when debugging or rolling back
- End with the standard attribution trailer

If the harness you are running under mandates its own additional `Co-Authored-By:` trailer, append it on its own line after the standard one. Do not replace the standard one.

---

## Step 5A — Execute (Path A, solo on main/master)

Execute as ONE chained command so the repo owner gets exactly one approval prompt:

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

Then go to Step 6.

---

## Step 5B — Execute (Path B, agent branch)

Path B ends at **"ready for the repo owner"**: a non-draft pull request with green checks. It does not merge. There is no step after Step 6 that you are allowed to add.

### 5B.1 — Commit and push the branch

One chained command, same message you wrote in Step 4:

```bash
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
git add -A && git commit -m "$(cat <<'EOF'
<title>

- <high-level change 1>
- <high-level change 2>

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)" && git push -u origin "$BRANCH"
```

`git push -u origin "$BRANCH"` pushes **your own branch only**. Never `git push origin HEAD:main`, never `git push origin main`, never `--force` in any form.

### 5B.2 — Check that `gh` is usable

```bash
command -v gh >/dev/null 2>&1 && gh auth status
```

If `gh` is missing, or `gh auth status` reports you are not logged in: **STOP here and report.** The branch is pushed and the work is safe. Say exactly this in your report:

> Branch `<branch>` is pushed. The pull request was NOT created because `gh` is unavailable. To finish: `gh pr create --draft --base <base> --head <branch> --title "<title>" --body-file <file>`, then `gh pr checks --watch`, then `gh pr ready`.

Do not fall back to the GitHub web UI, do not fall back to the REST API with a token you found, and do not treat the missing tool as a reason to merge locally.

### 5B.3 — Resolve the base branch

```bash
BASE="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"
```

If that comes back empty, STOP and report. Do not assume `main`.

### 5B.4 — Create the draft PR, or reuse the existing one

A branch can only have one open PR. Check before creating:

```bash
gh pr view "$BRANCH" --json number,url,state,isDraft
```

- Exits non-zero / "no pull requests found" → no PR yet, create one (below).
- Returns a PR with `"state": "OPEN"` → reuse it. Your new commit is already on it because you pushed the branch. If it is not a draft (`"isDraft": false`), convert it back to one first: `gh pr edit "$BRANCH" --draft`. Skip to 5B.5.
- Returns a PR with `"state": "MERGED"` or `"CLOSED"` → STOP and report. Someone else has moved this branch and you need the repo owner to say what happens next.

To create it, write the body to a file first so nothing in the markdown is re-read by the shell:

```bash
BODY_FILE="$(mktemp)"
cat > "$BODY_FILE" <<'EOF'
## What changed

- <high-level change 1>
- <high-level change 2>

## How it was verified

- <the check you ran and its result>

Ready for the repo owner to review and squash-merge. This PR was not merged by an agent and must not be.
EOF

gh pr create --draft --base "$BASE" --head "$BRANCH" \
  --title "<title>" --body-file "$BODY_FILE"
rm -f "$BODY_FILE"
```

`--draft` is required, not optional. The PR starts as a draft so that a half-finished push never looks reviewable.

Never add `--reviewer`, `--assignee`, or `--label` unless the ticket asked for it. Never use `--web` — there is no browser here.

### 5B.5 — Wait for checks

```bash
gh pr checks "$BRANCH" --watch --fail-fast --interval 15
echo "gh pr checks exit=$?"
```

`--watch` blocks until every check finishes. `--fail-fast` stops the watch the moment one check fails, instead of waiting out the rest. `--interval 15` polls every 15 seconds.

Read the exit code:

| Exit | Meaning | What you do |
| --- | --- | --- |
| `0` | All checks passed | Go to 5B.6 — mark it ready. |
| `1` + stderr says `no checks reported` | No checks are registered yet, OR this repo has no CI | Retry (below). |
| `1` otherwise | One or more checks FAILED | **STOP.** Leave the PR as a draft. Report which checks failed and the log output. Do not mark it ready. Do not merge. |
| `8` | Checks still pending | Should not happen with `--watch`. Treat as the retry case. |

**The retry case.** Right after a push, GitHub often reports no checks for a few seconds before the workflows register. Wait and look again, up to 3 times:

```bash
sleep 20
gh pr checks "$BRANCH" --watch --fail-fast --interval 15
```

If all 3 retries still say `no checks reported`, this repo has no CI on this branch. Proceed to 5B.6, and say plainly in your report: **"No CI checks ran on this PR — nothing verified it but the local build gate in Step 3."** If Step 3 found no build gate, say instead: **"No CI checks ran on this PR and there is no build gate — nothing verified it."**

### 5B.6 — Mark the PR ready for review

```bash
gh pr ready "$BRANCH"
gh pr view "$BRANCH" --json number,url,state,isDraft,mergeable
```

`gh pr ready` flips the PR out of draft. That is the handoff. It does not merge and it cannot merge.

### 5B.7 — Stop

You are done. The following are forbidden here and everywhere else in this command:

- `gh pr merge` — in any form, with or without `--auto`, `--squash`, `--merge`, `--rebase`, or `--admin`
- `git merge` — in either direction. Not your branch into `main`, and not `main` into your branch. If your branch is behind and needs the latest `main`, say so in your report and stop; the repo owner decides.
- `git push` to `main`, `master`, or any shared/integration branch
- `git reset`, `git rebase`, `git push --force`, `git push --force-with-lease`
- Enabling auto-merge through the API or the web UI
- Closing or deleting the branch to "clean up"

---

## Step 6 — Confirm the result

**Path A:** report the commit hash, the branch pushed, and the summary used.

**Path B:** report the commit hash, the branch pushed, the PR number and URL, whether the PR is now ready (non-draft), and the check result — passed, failed, or none ran. End with: **ready for the repo owner to review and squash-merge.** Never say the work is merged, landed, or shipped. It is not.
