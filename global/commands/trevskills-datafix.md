---
description: Run a prod data script (backfill, repair, sync) dev-first — dry run, snapshot, undo step, idempotence check, then the identical run on prod
---

This command is Trevor's explicit instruction to run a data script against the current repository's databases. It enforces the global rule: prod data scripts are allowed without asking, but only after the exact same change ran on dev in this session with no data loss or errors. Dev first, show the result, then prod.

**The prime directive: this command never destroys data.** If any step cannot be satisfied, stop and report. Stopping is always correct when a check fails.

**Never, at any step:**
- Deleting rows, unless the task explicitly asked for deletes (and then only those rows, named in the dry run).
- `prisma db push`, `prisma migrate *`, or any schema change. Schema work goes to `/trevskills-migrate`.
- Reading, cat-ing or grepping `.env.prod`, `.env.production` or `.env.staging`. Prod is reached only through `npx dotenv -e .env.prod --` in Steps 4-5.
- Port `:3001` is production. Steps 0-3 print the `DATABASE_URL` host and port only (never the password) and STOP if it contains `:3001`.

---

## Step 0 — Ground truth (read-only)

- Find the script (usually `scripts/<name>.ts`; onewitharts has ~28) or the task that needs one. Read it fully. Note how it loads env: in repos without `prisma.config.ts` (onewitharts) prefix with `npx dotenv -e .env.local --`.
- Resolve the dev `DATABASE_URL` from `.env.local` and print host and port only. Anything but dev: STOP.
- Write down the exact command and args. Dev and prod must run **this same command, same args**; only the env file differs.

## Step 1 — The script contract

A new or edited script must have all of these before it runs anywhere:

1. **Dry run by default.** With no flag it prints what would change, with row counts (matched, to change, to skip), and writes nothing. Writing needs an explicit `--apply`. A script that deletes rows snapshots the full deleted rows (every column), and its undo re-inserts them.
2. **Idempotent.** Selecting rows that still need the change means a second run matches 0 rows.
3. **Snapshot before write.** Before `--apply` touches a row, write the affected rows (ids + old values of every column it changes) to a JSON file, e.g. `scripts/snapshots/<name>-<env>-<timestamp>.json`. Do not commit snapshots that hold personal data; add the folder to `.gitignore`.
4. **Written undo.** The script's header comment (or a `--restore <snapshot.json>` mode) states exactly how to put the old values back from the snapshot. Undo updates by id and restores only the changed columns.
5. **Bounded writes.** Updates are by id, in one transaction per batch; the apply step aborts if it would touch more rows than the dry run reported.
6. **Pure transform tested.** Keep the row-to-new-value logic as a pure function, exported, with a test file next to the script (`x.ts` + `x.test.ts`, as onewitharts already does): changed row, already-correct row (no change), null/edge row. Run it with the repo's test runner and see it pass.

If the script lacks any of these, add them first (small edits only), and re-run the test.

## Step 2 — Dev run

Against dev only, in this order. Show the output of each:

1. **Before counts** (read-only): total rows in the table(s) and rows matching the fix.
2. **Dry run.** Confirm it wrote nothing (counts unchanged) and the numbers are sensible.
3. **Apply** (`--apply`). The snapshot file must exist and list the dry run's row count.
4. **After counts.** Total rows unchanged (unless deletes were asked for); changed rows equal the dry run's number.
5. **Re-run (dry run and apply)**: both must report **0 changes**. If not, the script is not idempotent: STOP.
6. Optionally test the undo on dev: restore from the snapshot, confirm counts return to the before numbers, then apply again and confirm the after numbers.

## Step 3 — Go/no-go gate

STOP and report instead of touching prod if ANY of these is true:

- Any Step 0-2 check failed or was skipped.
- Dev errored, or any count moved unexpectedly (rows lost, more rows changed than the dry run said).
- The script deleted anything the task did not ask for.
- The re-run changed rows.
- No snapshot or undo step exists.
- The prod command would differ from the dev command in anything but the env file.
- The dev run did not happen in this session. A dev run from an earlier session does not count.
- Anything was ambiguous or you had to guess.

A clean dev run in this session is the approval for prod. Never talk yourself past a failed check.

## Step 4 — Prod dry run (read-only)

Run the identical command, with no `--apply`, through `npx dotenv -e .env.prod --`. Report the host from the script's output if it prints one. Compare with dev:

- Counts are plausible against dev's. Prod having more rows is expected; say why the number makes sense.
- Any delete, or any write in a dry run: STOP.

## Step 5 — Prod apply

Run the identical command with `--apply` through `npx dotenv -e .env.prod --`.

- **Stop and report at once** on any error, on more rows changed than the Step 4 dry run said, or on any delete not asked for. Do not retry blindly.
- Keep the prod snapshot file; its path goes in the report.
- Then re-run the dry run on prod: it must report 0 changes. Report before/after counts.

If it fails midway, read the error, restore from the prod snapshot using the undo step (by id, old values), and report immediately.

## Step 6 — Report

- Script name, exact command and args, and what it changes in plain language.
- Test file result.
- Dev: before counts, dry run, apply, after counts, re-run showing 0 changes.
- Prod: dry run, apply, after counts, re-run showing 0 changes.
- Snapshot paths for dev and prod, and the undo command.
- If you stopped at the Step 3 gate or later, which check failed and what would clear it.
- **Remind Trevor to run `/trevskills-commitpush`** so the script and test are committed. Do not commit them yourself.
