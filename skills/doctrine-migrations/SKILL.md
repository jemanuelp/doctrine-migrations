---
name: doctrine-migrations
description: "Trigger: migraciones, Doctrine migrations, migrations.sh, schema change. Create, inspect, and run WhatsApp Bridge DB migrations."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

# Doctrine Migrations

## Activation Contract

Use this skill when creating, reviewing, executing, rolling back, or diagnosing Doctrine migrations in WhatsApp Bridge.

## Hard Rules

- Work from `migrations/`; this is a separate PHP Doctrine migrations project.
- Use `./migrations.sh <command> [args] [options]` as the only Doctrine entrypoint.
- Do not use TypeORM sync or ad-hoc schema mutation for schema evolution.
- Treat applied migration files as immutable; create a new migration for follow-up changes.
- Prefer canonical Doctrine command names (`migrations:status`) over shortened aliases (`status`).
- Before destructive commands (`migrations:execute --down`, `migrations:version --delete`, `migrations:rollup`), ask for explicit confirmation.
- When adding or changing NestJS entities, verify `api/src/database/entities.ts` includes them before generating diffs.
- Keep migration SQL explicit, reversible where possible, and compatible with the configured DB provider.
- For DDL, create one migration file per DDL statement: exactly one `$this->addSql(...)` in `up()` and exactly one in `down()`.
- For DML, multiple `$this->addSql(...)` calls are allowed in both `up()` and `down()`.
- Never mix DDL and DML in the same migration file; split schema changes and data changes into separate versions.
- Table and column names must follow the SQL object naming convention in `references/sql-object-naming-rules.md`: plural `snake_case` tables, singular `snake_case` columns, `id` primary keys, singular `<related_table>_id` foreign keys, `_at` timestamp fields, clear boolean prefixes, plural join tables without redundant `has`, and no reserved or ambiguous names.
- After `sh migrations.sh generate`, rename `VersionYYYYMMDDHHMMSS.php` to `VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php` and update the internal class name to match the file stem exactly.
- Run `scripts/validate_migration_names.py`, `scripts/validate_migration_file_rules.py`, and `scripts/validate_sql_object_names.py` before reporting migration work complete.

## Decision Gates

| Need | Action |
| --- | --- |
| Inspect state | Run `./migrations.sh migrations:status` and `./migrations.sh migrations:list`. |
| Create blank migration | Run `./migrations.sh migrations:generate`, then edit the generated file. |
| Generate from metadata diff | Run `./migrations.sh migrations:diff` only after entity metadata is correct. |
| Apply migrations | Run `./migrations.sh migrations:migrate` after status review. |
| Roll back or manually mark versions | Ask for confirmation first. |
| Migration has DDL and DML | Split it into separate schema and data migration files. |
| DDL migration has multiple statements | Split each DDL statement into its own migration file. |
| Migration creates or renames tables/columns | Enforce plural `snake_case` table names and singular `snake_case` column names from `references/sql-object-naming-rules.md`. |
| Migration creates a many-to-many table | Use plural table names joined by `_`, such as `users_roles`; avoid `users_has_roles` unless preserving existing schema. |
| Generated file is still bare `VersionYYYYMMDDHHMMSS.php` | Rename file and class with an English snake_case suffix. |
| Need naming-only enforcement | Run `python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py [path]`. |
| Need automated enforcement | Run `python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py [path]`. |
| Need SQL object naming enforcement | Run `python3 .agents/skills/doctrine-migrations/scripts/validate_sql_object_names.py [path]`. |
| Need exact command syntax | Open `references/doctrine-commands.md`. |

## Execution Steps

1. Verify the migration project is ready:
   ```bash
   cd migrations
   test -x migrations.sh || chmod +x migrations.sh
   ./migrations.sh migrations:status
   ```
2. For schema changes, inspect the relevant API entity/model change before generating or writing SQL.
3. Create or update the migration using the safest matching command from `references/doctrine-commands.md`.
4. Rename the generated file and class using `VersionYYYYMMDDHHMMSS_english_snake_case_suffix`.
5. Review the generated SQL manually; enforce `references/migration-file-rules.md` before running it.
6. Run `python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py <migration-file-or-dir>` from the repo root.
7. Run `python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py <migration-file-or-dir>` from the repo root.
8. Run `python3 .agents/skills/doctrine-migrations/scripts/validate_sql_object_names.py <migration-file-or-dir>` from the repo root.
9. Run `./migrations.sh migrations:status` and, when applying locally, `./migrations.sh migrations:migrate`.
10. Report the migration version, changed tables/columns/indexes, and verification command output.

## Output Contract

Return:

- Migration file path and version.
- Commands executed through `migrations.sh`.
- Tables, columns, indexes, constraints, or seed data affected.
- Confirmation that new or renamed tables and columns follow the SQL object naming convention.
- Filename and class name, confirming both match `VersionYYYYMMDDHHMMSS_english_snake_case_suffix`.
- Whether rollback SQL exists or why rollback is intentionally unavailable.
- Whether the file is DDL-only, DML-only, and compliant with addSql count rules.
- Validation output from `scripts/validate_migration_file_rules.py`.
- Naming validation output from `scripts/validate_migration_names.py`.
- SQL object naming output from `scripts/validate_sql_object_names.py`.
- Verification result from `migrations:status`, `migrations:list`, or `migrations:migrate`.

## References

- `references/doctrine-commands.md` — complete Doctrine migrations command catalog using `migrations.sh`.
- `references/migration-file-rules.md` — DDL/DML file structure rules and examples.
- `references/migration-file-examples.md` — complete DDL/DML migration examples.
- `references/many-to-many-table-examples.md` — join table naming SQL examples.
- `references/sql-object-naming-rules.md` — table, column, key, timestamp, boolean, and join table naming rules.
- `references/sql-object-naming-examples.md` — complete good and bad SQL object naming examples.
- `references/sql-object-naming-sql-examples.md` — complete SQL naming examples.
- `scripts/validate_migration_file_rules.py` — static checker for DDL/DML migration file rules.
- `scripts/validate_migration_names.py` — static checker for migration file and class names.
- `scripts/validate_sql_object_names.py` — static checker for SQL table and column naming rules.
