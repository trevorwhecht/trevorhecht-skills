---
description: Run a Prisma migration after full safety checks — reviewable SQL, a written rollback, zero data loss, no duplicate columns
---

This command is Trevor's explicit, deliberate instruction to run a Prisma migration for the current repository. It is the ONLY context in which `prisma migrate` is authorized — the global rule forbidding it is overridden by this invocation, for this invocation only.

It runs against the **dev** database first. Production is migrated by this same command in Step 8, and only after dev passes the Step 7 gate.

Still forbidden even here, no exceptions, no workarounds: `prisma migrate reset`, `--accept-data-loss`, `--force-reset`, and any hand-rolled equivalent (dropping and recreating the database, `TRUNCATE` to get past a constraint). The PreToolUse safety hook hard-blocks these. If one of them appears to be the only way forward, STOP and tell Trevor — do not route around the hook.

**`prisma db push` is never part of this command.** It is not authorized by this invocation and appears at no step. It applies a schema change with no migration file, which leaves nothing to deploy to production and nothing to roll back.

**The prime directive: this command never destroys data.** If any step below cannot be satisfied, stop and report. Stopping is always the correct outcome when a check fails.

---

## Step 0 — Establish the ground truth

Read-only. Do not skip; the rest of the command depends on knowing the real setup.

**0a — Target guard. This runs first and it is absolute.**

- **Port `:3001` is production.** Resolve the `DATABASE_URL` this command will use and print its host and port *only* (never the password). If it contains `:3001`, STOP. Every command in Steps 0–7 runs against DEV and nothing else.
- Steps 0–7 never read, source, or pass `.env.prod`, `.env.production`, or `.env.staging`. The dev URL comes from `.env.local` and nowhere else. `.env.prod` is used in Step 8 only.
- `prisma migrate reset`, `--accept-data-loss`, `--force-reset` and `prisma db push` are not part of this command at any step. The PreToolUse hook blocks the first three. If one of them looks like the only way forward, STOP and tell Trevor.
- In a Paperclip agent run (`$PAPERCLIP_AGENT_ID` is set), this ticket must be the repo's **schema-lane** ticket. If it is not, STOP and hand the issue back.

**0b — How this repo invokes the Prisma CLI.** This differs per repo and getting it wrong is how a command silently targets the wrong database.

- If `prisma.config.ts` exists (boisepartyco, quoting-template — Prisma 6.19), it names the schema path, the migrations path, and loads the dev env file itself. Plain `npx prisma …` is correct.
- If it does not exist (**onewitharts** — Prisma 5.22), the CLI loads **no** env file: there is no `.env` and no `prisma/.env`. Every Prisma command in this file must be prefixed with `npx dotenv -e .env.local --`, or it will fail to resolve `DATABASE_URL`. Prefix every `npx prisma …` below accordingly.
- Verified on 2026-10-06: `--from-schema-datasource` / `--to-schema-datasource` exist on both 5.22.0 and 6.19.3, so the Step 3 and Step 5 commands are the same on both. If a future upgrade removes them, `npx prisma migrate diff --help` lists the current spelling — check it, do not guess.

**0c — State of the change and the history.**

- `git status` and `git diff -- prisma/schema.prisma` — see exactly what schema change is being migrated. If `schema.prisma` has no changes and there are no unapplied migration folders, say so and stop.
- `npx prisma migrate status` — confirm the dev database has no failed migration and nothing unapplied. If there is a failed migration, STOP and report it. Drift is resolved by conversation with Trevor, never by resetting.
- `npx prisma validate` — the schema must be valid before anything else happens.
- **Drift baseline.** Before this change, dev must already match the schema it started from. Otherwise Step 3's diff mixes old drift into this migration, and Step 6.4 can never pass. Diff dev against the schema as it was **before** this change: the merge-base with the branch this work is based on. Use the branch the caller named (`/trevskills-scrum` passes `base=<its job's BASE>`, e.g. `origin/finalchanges2`). Only when none was named, use `origin/HEAD` (run `git remote set-head origin -a` if it's missing). Never assume `main`: a feature branch based elsewhere would show that branch's whole schema history as drift.
  ```bash
  base=$(git merge-base HEAD "${BASE_REF:-origin/HEAD}"); tmp=$(mktemp -d)   # BASE_REF = the named base branch
  git show "$base:prisma/schema.prisma" > "$tmp/base.prisma"
  npx prisma migrate diff --from-schema-datasource prisma/schema.prisma \
    --to-schema-datamodel "$tmp/base.prisma" --script
  ```
  Empty output means no drift; carry on. Any statement is **pre-existing drift**. It is never folded into this migration. STOP and report each statement on its own, with which old migration caused it and the fix. The default fix is to make `schema.prisma` describe what the database really has, as its own small change, before this migration runs again:
  - The database has a default the schema lacks → add it to the field (e.g. `@default(now()) @updatedAt`).
  - The database has something Prisma can't express (a partial or expression index, a `CHECK`): the schema must not declare a conflicting attribute (no `@unique` that would create a second, full index). Add a comment on the field naming the migration that holds the raw SQL.
- **No new drift.** Whenever this command hand-edits `migration.sql` (a rename fix, a partial index, anything Prisma can't express), it updates `schema.prisma` in the same run so the two still agree. Step 6.4's `--exit-code` check enforces that before the gate.
- `ls prisma/migrations` and record the newest folder whose name starts with 14 digits:
  ```bash
  ls prisma/migrations | grep -E '^[0-9]{14}_' | sort | tail -1
  ```
  You need this value in Step 3 and Step 6b.

**0d — Known limit, state it in the report.** Step 3 derives the SQL from the **live dev database**, not by replaying the migration folders. In onewitharts a replay is not available (`migrate dev` fails with P3006 — the shadow-database replay cannot reproduce that history), so this command cannot prove dev and production have the same shape. What it does prove is that the SQL moves *this* database to the schema in `schema.prisma`. If production's shape differs, Step 8's `migrate deploy` errors on that statement and stops. Say this plainly in the report; do not imply the migration was verified against production.

Report what you found before proceeding.

## Step 1 — Duplicate-column check

Before generating any SQL, prove the change is not re-adding data the schema already holds. For every field being added:

- Grep the model for a field with the same meaning under a different name (`phone` vs `phoneNumber`, `createdAt` vs `dateCreated`, `isActive` vs `status`). Near-synonyms are the common failure.
- Check whether the value is already derivable from an existing relation — a scalar copied off a related row (`order.customerEmail` when `order.user.email` exists) is duplicated data, not a new column.
- Check the other models for the same field. If the same data now lives on two tables, one of them is a denormalization that needs a stated reason.
- Confirm no redundant relation scalar: Prisma already gives you the foreign key field, so a second column holding the same id is a duplicate.

If anything looks duplicated, STOP and present the finding with the alternative (reuse the existing column / read through the relation). Trevor decides; do not migrate a duplicate on your own judgment.

## Step 2 — Prisma good-practices review of the schema change

Check the changed models against these before generating SQL. Report violations; apply only the fixes Trevor approves.

- **Every model has a stable `@id`** — `cuid()`/`uuid()` for anything externally visible, never a natural key that can change.
- **Relations are explicit and indexed.** Every foreign key scalar used in a `where` or a join needs `@@index([fk])` — Postgres does not create one automatically for the referencing side, and this is the single most common cause of a table that gets slow later.
- **`onDelete` is stated deliberately** on every relation (`Cascade`, `Restrict`, `SetNull`). Leaving it implicit turns into a runtime error at delete time; decide it now, not in production.
- **Optional vs required matches reality.** Per the global performance rules: prefer nullable fields and soft deletes over storing duplicate state. A new required field on a table that already has rows is the #1 source of a failed migration — see Step 4.
- **Money is `Decimal`, never `Float`.** Timestamps are `DateTime` with `@default(now())` / `@updatedAt` where they mean creation/modification.
- **Enums over free-text status strings** when the set is closed and known.
- **`@unique` / `@@unique` reflect a real business invariant**, and the existing rows already satisfy it — adding a unique constraint to a column with duplicate values fails mid-migration.
- **Field names are `camelCase` in the schema**; use `@map`/`@@map` if the database column must differ, rather than renaming the Prisma field.
- **Nothing is added that isn't needed** — no column "for later." Same YAGNI rule that applies to code, and a speculative column is far harder to remove than to add.

## Step 3 — Generate the migration WITHOUT applying it

**Do not use `prisma migrate dev --create-only`.** It builds a shadow database by replaying every
folder in `prisma/migrations/`, and in onewitharts that replay fails (P3006). The drift-safe
sequence is `migrate diff` → `db execute` → `migrate resolve --applied`: diff here in Step 3,
execute and resolve in Step 6.

```bash
name="$(date -u +%Y%m%d%H%M%S)_<snake_case_descriptive_name>"
mkdir -p "prisma/migrations/$name"
npx prisma migrate diff \
  --from-schema-datasource prisma/schema.prisma \
  --to-schema-datamodel  prisma/schema.prisma \
  --script > "prisma/migrations/$name/migration.sql"
```

`--from-schema-datasource` reads the **live dev database**; `--to-schema-datamodel` reads the
**edited schema file**. The output is the SQL that moves dev to the new shape. `migrate diff` is
read-only — it writes nothing to any database, which is what makes the migration reviewable before
it touches data. Never generate and apply in one step.

Then check three things before you go on:

1. **The file is not empty.** An empty `migration.sql` means dev already has the change (someone
   ran `db push`, or the migration is already applied under another name). STOP and report — do not
   commit an empty folder.
2. **The timestamp sorts last.** `$name` must sort strictly after the newest 14-digit folder you
   recorded in Step 0c, and after the newest one on `origin/main`:
   ```bash
   latest=$(git ls-tree --name-only origin/main prisma/migrations/ \
     | xargs -n1 basename | grep -E '^[0-9]{14}_' | sort | tail -1)
   [[ "$name" > "$latest" ]] || echo "RE-TIMESTAMP NEEDED — see Step 6b"
   ```
   Compare against 14-digit names only. onewitharts has two legacy folders with no timestamp
   (`add_designimage_and_colorvariant_to_mockup_1783204670`,
   `add_favorite_blanks_column_1757802190871`) that sort after every numeric name; including them
   would make the check impossible to pass. They are applied history and are left alone.
3. **The name says what it does** (`add_order_guests_field`, `backfill_user_phone`), matching the
   existing names in `prisma/migrations/`.

## Step 4 — Read the SQL and scan it for data loss

Read the generated `migration.sql` in full. Flag every one of these:

| Pattern in the SQL | Why it's dangerous |
|---|---|
| `DROP TABLE` | Destroys a table's data outright. |
| `DROP COLUMN` | Destroys that column's data outright. |
| `ADD COLUMN ... NOT NULL` with no `DEFAULT` | Fails immediately on any table that already has rows. |
| `ALTER COLUMN ... SET NOT NULL` | Fails if any existing row is null. |
| `ALTER COLUMN ... TYPE` | Silently truncates or fails, depending on the narrowing. |
| `DROP ... ADD` on a pair of similarly-named columns | **A rename Prisma didn't detect.** Prisma has no rename detection — renaming a field in the schema always emits drop-then-add, which throws the data away. Hand-edit the SQL to `ALTER TABLE "T" RENAME COLUMN "old" TO "new";` and delete the drop/add pair. |
| `ADD CONSTRAINT ... UNIQUE` / `CREATE UNIQUE INDEX` | Fails if existing rows already collide. |
| `DROP CONSTRAINT` / `DROP INDEX` | Not data loss, but check it isn't the only thing enforcing an invariant. |
| `TRUNCATE`, `DELETE FROM` | Never acceptable in a generated migration. |

For every flagged statement, run a read-only count against the **dev** database before continuing:

```sql
SELECT count(*) FROM "Table";                          -- rows at risk
SELECT count(*) FROM "Table" WHERE "col" IS NULL;      -- before SET NOT NULL
SELECT "col", count(*) FROM "Table"                    -- before adding UNIQUE
  GROUP BY "col" HAVING count(*) > 1;
```

Use `npx prisma studio` or a read-only query; never mutate to "clean up" during this step.

**Production counts are taken in Step 8**, read-only, immediately before the production deploy.

A dev count of zero proves nothing about production. A
statement flagged above is treated as dangerous on its row count **or** on the possibility that
production has rows dev does not. When in doubt, expand-and-contract.

**If any flagged statement would touch a non-zero dev row count — or could plausibly touch rows in production — rewrite the migration as expand-and-contract instead:**

1. **Expand** — add the new column as nullable (or with a default). Deploy. Nothing breaks; old code still works.
2. **Backfill** — a separate migration (schema: `/trevskills-migrate`) or a data script (`/trevskills-datafix`) that copies data into the new shape, written to be safely re-runnable.
3. **Migrate the code** — application reads and writes the new column. Deploy.
4. **Contract** — a later migration, once the new column is proven in production, that drops the old one.

Each phase is its own migration and its own commit. This is slower, and it is the only way a rename, a type change, or a new required column happens without downtime or loss.

Also check for a lock hazard: on a large Postgres table, `CREATE INDEX` blocks writes for the duration. If the table is large, put `CREATE INDEX CONCURRENTLY` in a migration of its own — Prisma wraps a migration file in a transaction and `CONCURRENTLY` cannot run inside one, so it must be the only statement in that file.

## Step 5 — Write the rollback

Prisma has no automatic down migrations. Generate one now, **while the database is still in the pre-migration state** — this is the only moment it can be produced automatically:

```bash
npx prisma migrate diff \
  --from-schema-datamodel prisma/schema.prisma \
  --to-schema-datasource prisma/schema.prisma \
  --script > "prisma/migrations/$name/down.sql"
```

`--from-schema-datamodel` reads the new, edited schema file; `--to-schema-datasource` reads the live (still old) database. The output is the SQL that returns the database to its current shape. It is the exact reverse of the Step 3 diff, which is why it must be generated **now** — after Step 6 applies the change, the datasource is no longer the pre-migration state and this command produces nothing.

**If `down.sql` cannot be produced, the migration is not ready.** Stop. Do not apply an up migration you cannot reverse.

Then **read `down.sql` and judge whether it is honest**:

- If the up migration only added things, the down cleanly removes them. Good.
- If the up migration dropped or altered anything, the down **cannot restore the data** — it only restores the structure. Say so explicitly in the report. A rollback that silently loses data is worse than no rollback.
- If `down.sql` would itself destroy data the up migration created, note the trade-off.

Commit `down.sql` alongside `migration.sql`. It is applied manually with `npx prisma db execute --file <path>` followed by `npx prisma migrate resolve --rolled-back <migration_name>` — never by editing the migration folder after the fact.

## Step 6 — Apply to the dev database

**Do not use `prisma migrate dev`.** Same reason as Step 3: it replays the whole history into a
shadow database and fails in onewitharts. Apply the reviewed SQL directly, then record it as
applied so `_prisma_migrations` and Step 8's `migrate deploy` agree with the folder on disk.

**6.1 — Apply the SQL.** `prisma db execute` does **not** wrap the script in a transaction, so a
multi-statement migration can half-apply. Wrap it at execute time, without editing the file —
`migration.sql` must stay exactly as Step 8 will apply it to production, and `migrate deploy` adds its own
transaction:

```bash
if grep -qi 'CONCURRENTLY' "prisma/migrations/$name/migration.sql"; then
  # CREATE INDEX CONCURRENTLY cannot run inside a transaction, and must be the
  # only statement in the file (see the lock hazard note in Step 4).
  npx prisma db execute --file "prisma/migrations/$name/migration.sql" --schema prisma/schema.prisma
else
  { echo 'BEGIN;'; cat "prisma/migrations/$name/migration.sql"; echo 'COMMIT;'; } \
    | npx prisma db execute --stdin --schema prisma/schema.prisma
fi
```

If this errors, the transaction rolled the change back and `_prisma_migrations` was never touched.
STOP and report the error. Do not run Step 6.2.

**6.2 — Record it as applied.**

```bash
npx prisma migrate resolve --applied "$name"
```

This writes the row into `_prisma_migrations` without re-running the SQL. Run it only after 6.1
succeeded — recording a migration that did not apply is how the history and the database come
apart.

**6.3 — Regenerate the client.**

```bash
npx prisma generate
```

**6.4 — Verify. Do not assume.**

- `npx prisma migrate status` → the new migration is applied, nothing pending, nothing failed.
- The database now matches the schema file. This must exit `0`:
  ```bash
  npx prisma migrate diff \
    --from-schema-datasource prisma/schema.prisma \
    --to-schema-datamodel  prisma/schema.prisma \
    --exit-code
  ```
  Exit `2` means a difference remains — the migration is incomplete. STOP.
- Re-run the dev row counts from Step 4 on every affected table and **compare against the before numbers**. Any drop in a count that wasn't explicitly intended is a failure — report it immediately.
- `npx prisma validate`, then `npx tsc --noEmit` to confirm the regenerated client still matches the application code. **Do not run `npm run build`** — it overwrites `.next` and wedges Trevor's running dev server.
- Run the test suite if the project has one (`npm test`).

## Step 6b — Re-timestamp a branch-only migration

Use this **only** when Step 3's ordering check failed, or when `main` gained a migration after
yours was created. Both cases mean your folder no longer sorts last, and Prisma applies folders in
name order — so on a fresh replay yours would run before a migration it depends on.

**The timestamp rule.** A new folder's timestamp is `date -u +%Y%m%d%H%M%S` at the moment it is
created, and it must sort **strictly after the newest 14-digit folder on `origin/main`**. Compare
against 14-digit names only; onewitharts' two legacy un-timestamped folders are excluded (Step 3).
If the clock value does not already beat `$latest` — because a folder on main carries a
future-dated timestamp — use `$latest` plus one second instead. Never pad it further than that, and
never reuse an existing timestamp: onewitharts already has three timestamps shared by more than one
folder, which is half of why its ordering is broken.

**First: do the two histories touch the same tables?** `git fetch origin main`, read the new
`migration.sql` files on main, and compare their tables to yours.

**Different tables — rename in place.**

1. `git mv prisma/migrations/$old prisma/migrations/$new`
2. On **DEV only**, point the history row at the new name. Confirm the target is dev before you run
   it (Step 0a); this statement must never reach production:
   ```bash
   echo "UPDATE \"_prisma_migrations\" SET migration_name = '$new' WHERE migration_name = '$old';" \
     | npx prisma db execute --stdin --schema prisma/schema.prisma
   ```
   The checksum column is computed from `migration.sql`, which did not change, so it stays valid.
3. `npx prisma migrate status` → still clean, nothing pending.
4. Re-run the Step 3 ordering check. It must pass now.

**Same tables — unwind and redo.** A rename is not safe here; the SQL itself was written against
the wrong starting shape.

1. Apply the rollback on dev: `npx prisma db execute --file "prisma/migrations/$old/down.sql" --schema prisma/schema.prisma`
2. `npx prisma migrate resolve --rolled-back "$old"`
3. Delete the folder: `git rm -r "prisma/migrations/$old"`
4. `git merge --no-edit origin/main` (never rebase), then apply main's new migrations to dev.
5. Redo the migration from Step 3 with a fresh timestamp.

**Never re-timestamp a migration that is applied to production or merged to `main`.** At that point
it is history — fix it forward with a new migration. Step 6b applies to a branch-only folder and
nothing else.

## Step 7 — The go/no-go gate

**A clean dev run IS the approval for production.** Step 8 applies the migration to production only if every item below is clear.

That makes this gate the thing standing between a schema change and live data. Treat it accordingly. **STOP and report instead of handing off if ANY of these is true:**

- Any check in Steps 0–5 failed, or was skipped for any reason.
- The Step 0a target guard did not run, or the resolved `DATABASE_URL` was anything other than dev.
- `migration.sql` came out empty, or `down.sql` could not be produced.
- Step 6.1 errored, Step 6.2 was run without 6.1 succeeding, or `migrate status` shows anything pending or failed afterward.
- The Step 6.4 `migrate diff --exit-code` did not exit `0`. A remaining difference means the migration does not finish the job.
- A dev row count dropped in a way that wasn't the explicit, intended point of the migration.
- The type check (`npx tsc --noEmit`) failed.
- The test suite failed — or the project has tests and they weren't run.
- Step 3's ordering check failed and Step 6b was not run, or was run and the check still fails.
- You hand-edited `migration.sql` (a rename fix, an expand/contract split) and haven't re-applied it to dev since.
- Step 4 flagged a destructive statement and you cannot say, in one sentence, why production is safe.
- Anything at all was ambiguous or you had to guess.

This gate replaces Trevor's manual approval. Nothing prompts you any more, so nothing but this
list stops a bad migration. Never talk yourself past a failed check.

Ambiguity counts as a failure. Stopping costs nothing; a bad prod migration costs everything.

## Step 8 — Apply to production

Runs only when the Step 7 gate is fully clear. Same prime directive: no data loss.

**8.1 — Target and status (read-only).** Run `npx dotenv -e .env.prod -- npx prisma migrate status`
and report the host from its `Datasource "db": ... at "<host>"` line. Never read, cat, grep or source
`.env.prod` directly: the project denies reading it, and that denial parks headless jobs. The pending list must be exactly the
migration(s) this run created, or migrations you can name and have read. A failed migration, or an
unexpected pending one, is a STOP — report it.

**8.2 — Destructive check.** For each pending `migration.sql` statement that is `DROP TABLE/COLUMN/SCHEMA`,
`TRUNCATE`, `DELETE FROM`, or a column type change, run a read-only prod query. The statement is
**obviously safe** and deploys with no stop when either:
- every table it touches has **0 rows** in production, or
- it is a type change, and a read-only query proves every existing non-null value converts without
  loss. Examples: text → enum, where `SELECT DISTINCT col` lists only enum labels. int → bigint.
  float → decimal, where no value has more digits than the new precision/scale allows. Give the query
  and its result in the report.

Anything else (a DROP or TRUNCATE on a table with rows, a narrowing cast, a cast you can't prove)
is a STOP: show Trevor the SQL. It goes to production only after he approves that specific
migration. A caller can pass `prod-approved=<sha>`; it counts as that approval only when it equals
`cat <the pending migration.sql files> | shasum -a 256 | cut -c1-12`, run in pending order. When
you stop, print that sha on its own line as `prod-approval-sha: <sha>`.

**8.3 — Before counts (read-only).** Row counts on every table the migration touches, plus a
column/index existence check for what it adds.

**8.4 — Deploy.** `npx dotenv -e .env.prod -- npx prisma migrate deploy`. It applies each pending
migration in its own transaction and records it. Nothing else touches production: never
`migrate dev` or `db push`, and none of the forbidden flags listed at the top of this file.

**8.5 — Verify.** `migrate status` → up to date. Re-run the 8.3 counts: every count unchanged
unless the migration's stated purpose changes it. The added column/index now exists.

**Ship order matters:** an **additive** migration goes to production before or with the code that
uses it — deployed code that reads a column production lacks takes the site down. A **contract**
migration (dropping what old code still reads) goes only after the code that stopped reading it is
live.

**If a production deploy fails mid-way:** do not retry blindly. Read the error, apply `down.sql`
with `npx dotenv -e .env.prod -- npx prisma db execute --file <path> --schema prisma/schema.prisma`
if the structure needs reverting, run `migrate resolve --rolled-back <name>`, and report
immediately.

## Step 9 — Report

One report at the end covering the whole run:

- The migration name and path, and what changed in plain language.
- The duplicate-column and good-practice findings, including anything still open.
- The data-loss scan: which statements were flagged, the **dev** row counts involved, and what was done about them. Include the production before/after counts from Step 8.
- Whether `down.sql` restores structure only, or structure and data.
- Dev verification: `migrate status`, the Step 6.4 `--exit-code` result, before/after counts, `tsc`, tests.
- Ordering: the timestamp used, the newest 14-digit folder on `origin/main` it has to beat, and whether Step 6b was needed.
- Production: what `migrate deploy` applied, `migrate status`, and the before/after counts.
- **Remind Trevor to run `/trevskills-commitpush`** so the migration folder is committed. Do not commit it yourself.
- If you stopped at the Step 7 gate instead of handing off, say exactly which check failed and what it would take to clear it.

---

**Never edit a migration that has been applied to production or merged to `main`.** At that point it
is history — fix it forward with a new migration. The one exception is a **branch-only** folder that
exists nowhere but your working branch and the dev database: that may be re-timestamped, or rolled
back and redone, under Step 6b and nowhere else.
