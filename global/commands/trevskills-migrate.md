---
description: Run a Prisma migration after full safety checks — reviewable SQL, a written rollback, zero data loss, no duplicate columns
---

This command is Trevor's explicit, deliberate instruction to run a Prisma migration for the current repository. It is the ONLY context in which `prisma migrate` / `prisma db push` are authorized — the global rule forbidding them is overridden by this invocation, for this invocation only.

Still forbidden even here, no exceptions, no workarounds: `prisma migrate reset`, `--accept-data-loss`, `--force-reset`, and any hand-rolled equivalent (dropping and recreating the database, `TRUNCATE` to get past a constraint). The PreToolUse safety hook hard-blocks these. If one of them appears to be the only way forward, STOP and tell Trevor — do not route around the hook.

**The prime directive: this command never destroys data.** If any step below cannot be satisfied, stop and report. Stopping is always the correct outcome when a check fails.

---

## Step 0 — Establish the ground truth

Read-only. Do not skip; the rest of the command depends on knowing the real setup.

- `git status` and `git diff -- prisma/schema.prisma` — see exactly what schema change is being migrated. If `schema.prisma` has no changes and there are no unapplied migration folders, say so and stop.
- Read `prisma.config.ts` (or `package.json#prisma`) to learn the schema path, migrations path, and **which env file the dev database URL comes from**. Trevor's projects typically load `.env.local` for dev and keep production in `.env.prod`.
- `npx prisma migrate status` — confirm the dev database is in sync with no failed or missing migrations. If there is drift or a failed migration, STOP and report it. Drift is resolved by conversation with Trevor, never by resetting.
- `npx prisma validate` — the schema must be valid before anything else happens.

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

```bash
npx prisma migrate dev --create-only --name <snake_case_descriptive_name>
```

`--create-only` writes `prisma/migrations/<timestamp>_<name>/migration.sql` and applies nothing. This is what makes the migration reviewable before it touches data. Never generate and apply in one step.

Name the migration for what it does (`add_order_guests_field`, `backfill_user_phone`), matching the existing names in `prisma/migrations/`.

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

For every flagged statement, run a read-only count against the dev database **and** against production before continuing — an empty dev table proves nothing about the live data:

```sql
SELECT count(*) FROM "Table";                          -- rows at risk
SELECT count(*) FROM "Table" WHERE "col" IS NULL;      -- before SET NOT NULL
SELECT "col", count(*) FROM "Table"                    -- before adding UNIQUE
  GROUP BY "col" HAVING count(*) > 1;
```

Use `npx prisma studio` or a read-only query; never mutate to "clean up" during this step.

**If any flagged statement would touch a non-zero row count, rewrite the migration as expand-and-contract instead:**

1. **Expand** — add the new column as nullable (or with a default). Deploy. Nothing breaks; old code still works.
2. **Backfill** — a separate migration or script that copies data into the new shape, written to be safely re-runnable.
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
  --script > prisma/migrations/<timestamp>_<name>/down.sql
```

`--from-schema-datamodel` reads the new, edited schema file; `--to-schema-datasource` reads the live (still old) database. The output is the SQL that returns the database to its current shape.

Then **read `down.sql` and judge whether it is honest**:

- If the up migration only added things, the down cleanly removes them. Good.
- If the up migration dropped or altered anything, the down **cannot restore the data** — it only restores the structure. Say so explicitly in the report. A rollback that silently loses data is worse than no rollback.
- If `down.sql` would itself destroy data the up migration created, note the trade-off.

Commit `down.sql` alongside `migration.sql`. It is applied manually with `npx prisma db execute --file <path>` followed by `npx prisma migrate resolve --rolled-back <migration_name>` — never by editing the migration folder after the fact.

## Step 6 — Apply to the dev database

```bash
npx prisma migrate dev
npx prisma generate
```

Then verify; do not assume:

- `npx prisma migrate status` → migration applied, nothing pending, nothing failed.
- Re-run the row counts from Step 4 on every affected table and **compare against the before numbers**. Any drop in a count that wasn't explicitly intended is a failure — report it immediately.
- `npx prisma validate`, then a build/type check (`npm run build` or `npx tsc --noEmit`) to confirm the regenerated client still matches the application code.
- Run the test suite if the project has one (`npm test`).

## Step 7 — The go/no-go gate

**A clean dev run IS the approval for production.** Trevor does not approve prod separately — if every check below is green, continue straight to Step 8 in the same run, without pausing to ask.

That makes this gate the thing standing between a schema change and live data. Treat it accordingly. **STOP and report instead of deploying if ANY of these is true:**

- Any check in Steps 0–5 failed, or was skipped for any reason.
- The dev migration errored, or `migrate status` shows anything pending or failed afterward.
- A dev row count dropped in a way that wasn't the explicit, intended point of the migration.
- The build or type check failed.
- The test suite failed — or the project has tests and they weren't run.
- The Step 4 counts **against production** showed rows that would be dropped, or rows that would violate a constraint the migration adds. Dev passing proves nothing here; prod data is the data that matters.
- You hand-edited `migration.sql` (a rename fix, an expand/contract split) and haven't re-run Step 6 against dev since.
- Anything at all was ambiguous or you had to guess.

Ambiguity counts as a failure. Stopping costs nothing; a bad prod migration costs everything.

## Step 8 — Production (runs automatically once Step 7 is green)

1. **Back up first — this is now the load-bearing safety step.** It replaced Trevor's manual approval, so it is not a formality:
   ```bash
   pg_dump "$PROD_DATABASE_URL" -Fc -f backup-$(date +%Y%m%d-%H%M%S).dump
   ls -lh backup-*.dump
   ```
   Confirm the file exists and is non-empty. **If `pg_dump` fails, is unavailable, or produces an empty dump, STOP — do not deploy.** The only acceptable substitute is a confirmed provider point-in-time-recovery window that covers this moment; if you rely on that, say so explicitly in the report.
2. **Check the target before writing to it:**
   ```bash
   dotenv -e .env.prod -- npx prisma migrate status
   ```
   It must show exactly the expected pending migration(s), no failures, no drift. **Any surprise here is a STOP** — production having a state you didn't predict means your dev-based reasoning doesn't apply to it.
3. **Deploy** — `migrate deploy` only. It applies existing migration files and never generates, prompts, or resets:
   ```bash
   dotenv -e .env.prod -- npx prisma migrate deploy
   ```
4. **Verify** — `migrate status` again, and re-run the Step 4 row counts against production, comparing to the before numbers. Report the actual numbers, not "looks fine."
5. **If it fails mid-way:** do not retry blindly and do not reset. Read the error, apply `down.sql` with `npx prisma db execute --file` if the structure needs reverting, `npx prisma migrate resolve --rolled-back <name>`, and report immediately. Restoring from the Step 8.1 backup is Trevor's call, not yours.

## Step 9 — Report

One report at the end covering the whole run:

- The migration name and path, and what changed in plain language.
- The duplicate-column and good-practice findings, including anything still open.
- The data-loss scan: which statements were flagged, the dev **and** prod row counts involved, and what was done about them.
- Whether `down.sql` restores structure only, or structure and data.
- Dev verification: migrate status, before/after counts, build, tests.
- Production: backup filename and size, migrate status before and after, before/after row counts.
- **Remind Trevor to run `/trevskills-commitpush`.** `migrate deploy` reads the migration files from the working tree, not from git, so production may now be running a migration that isn't committed yet — the repo needs to catch up so prod's schema is reproducible. Do not attempt to commit it yourself; `/trevskills-commitpush` is his to invoke.
- If you stopped at the Step 7 gate instead of deploying, say exactly which check failed and what it would take to clear it.

---

**Never edit a migration that has already been applied anywhere.** Once it is in `_prisma_migrations`, it is history — fix it forward with a new migration.
