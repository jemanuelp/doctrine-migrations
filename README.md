# Doctrine Migrations Skill

OpenCode skill for creating, reviewing, executing, rolling back, and diagnosing Doctrine migrations in WhatsApp Bridge.

The skill enforces a conservative migration workflow: use the Doctrine wrapper, keep applied migrations immutable, split schema changes from data changes, and validate migration file structure before reporting work as complete.

## What It Does

- Routes Doctrine migration work through `./migrations.sh`.
- Documents the safe command set for inspecting, generating, applying, and rolling back migrations.
- Enforces migration file naming with an English `snake_case` suffix.
- Documents SQL object naming conventions for tables, columns, primary keys, foreign keys, timestamps, booleans, and join tables.
- Enforces one DDL statement per DDL migration file.
- Prevents mixing DDL and DML in the same migration version.
- Provides Python validators for naming and file-structure checks.

## Repository Layout

```text
skills/doctrine-migrations/
  SKILL.md
  references/
    doctrine-commands.md
    migration-file-rules.md
    migration-file-examples.md
    many-to-many-table-examples.md
    sql-object-naming-rules.md
    sql-object-naming-examples.md
    sql-object-naming-sql-examples.md
  scripts/
    validate_migration_file_rules.py
    validate_migration_names.py
```

## Installation

Install the skill with:

```bash
npx skills add jemanuelp/doctrine-migrations
```

Install this repository as an OpenCode skill source, or copy `skills/doctrine-migrations` into your OpenCode skills directory.

Common local layout:

```text
~/.config/opencode/skills/doctrine-migrations/
```

The skill should be available as `doctrine-migrations` after OpenCode refreshes its skill registry.

## When To Use It

Use this skill for requests involving:

- Doctrine migrations
- `migrations.sh`
- Database schema changes
- Migration generation, review, execution, rollback, or diagnosis
- WhatsApp Bridge migration workflow

## Core Workflow

From the target application repository:

1. Inspect migration state.

   ```bash
   cd migrations
   ./migrations.sh migrations:status
   ./migrations.sh migrations:list
   ```

2. Create a blank migration when writing SQL manually.

   ```bash
   ./migrations.sh migrations:generate
   ```

3. Generate from metadata only after confirming the API entity metadata is correct.

   ```bash
   ./migrations.sh migrations:diff
   ```

4. Rename generated files from the bare Doctrine name to the required project shape.

   ```text
   VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php
   ```

5. Update the internal class name to exactly match the file stem.

6. Validate the migration file or directory.

   ```bash
   python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py migrations/migrations
   python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py migrations/migrations
   ```

7. Apply locally only after reviewing status and SQL.

   ```bash
   ./migrations.sh migrations:migrate
   ./migrations.sh migrations:status
   ```

## Migration Rules

### Naming

Migration files and classes must use this format:

```text
VersionYYYYMMDDHHMMSS_english_snake_case_suffix
```

Good examples:

```text
Version20250325180154_add_integration_column_to_instance_table.php
Version20250108163808_create_message_context_info_table.php
Version20250319164423_alter_media_data_drop_not_null_disappearing_mode_initiator.php
```

Bad examples:

```text
Version20250325180154.php
Version20250325180154AddIntegrationColumnToInstanceTable.php
```

### DDL

DDL migrations change schema, such as `CREATE`, `ALTER`, `DROP`, constraints, indexes, or foreign keys.

Rules:

- One migration file per DDL statement.
- Exactly one `$this->addSql(...)` call in `up()`.
- Exactly one `$this->addSql(...)` call in `down()`.
- No data changes in the same file.

### SQL Object Naming

DDL migrations that create or rename database objects must follow `skills/doctrine-migrations/references/sql-object-naming-rules.md`:

- Tables use plural `snake_case`, such as `users`, `products`, `orders`, and `order_items`.
- Columns use singular `snake_case`, such as `email`, `phone_number`, `status`, and `total_amount`.
- Primary keys use `id` inside each table.
- Foreign keys use the related entity in singular form plus `_id`, such as `user_id`, `product_id`, and `order_id`.
- Timestamp fields that represent events should end in `_at`, such as `created_at`, `updated_at`, `deleted_at`, and `paid_at`.
- Boolean fields should express a condition, such as `is_active`, `is_deleted`, `has_discount`, or `can_login`.
- Many-to-many join tables combine the related plural table names, such as `users_roles` and `products_categories`; avoid redundant names such as `users_has_roles`.
- Avoid `camelCase`, reserved words, ambiguous names, overly generic names, and fields that store multiple values.

### DML

DML migrations change data, such as `INSERT`, `UPDATE`, `DELETE`, or backfills.

Rules:

- Multiple `$this->addSql(...)` calls are allowed.
- Related data changes may stay together when they are one logical change.
- Rollback SQL should reverse the exact effect where feasible.
- No schema changes in the same file.

## Validators

### Naming Validator

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py [path]
```

Checks that:

- File names include an English `snake_case` suffix.
- Class names include the same suffix.
- File stem and class name match exactly.

### File Rule Validator

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py [path]
```

Checks that:

- Migration files are DDL-only or DML-only.
- DDL migrations contain exactly one SQL statement in `up()` and `down()`.
- DML migrations do not contain schema-changing statements.
- SQL statements can be classified as DDL or DML.

## References

- `skills/doctrine-migrations/SKILL.md` is the runtime contract for agents.
- `skills/doctrine-migrations/references/doctrine-commands.md` lists supported Doctrine commands through `migrations.sh`.
- `skills/doctrine-migrations/references/migration-file-rules.md` explains naming and DDL/DML separation rules.
- `skills/doctrine-migrations/references/migration-file-examples.md` contains complete DDL/DML migration examples.
- `skills/doctrine-migrations/references/many-to-many-table-examples.md` contains many-to-many join table naming examples.
- `skills/doctrine-migrations/references/sql-object-naming-rules.md` explains table, column, key, timestamp, boolean, and join table naming rules.
- `skills/doctrine-migrations/references/sql-object-naming-examples.md` contains complete good and bad SQL object naming examples.
- `skills/doctrine-migrations/references/sql-object-naming-sql-examples.md` contains complete SQL naming examples.
- `skills/doctrine-migrations/scripts/validate_migration_names.py` validates file and class names.
- `skills/doctrine-migrations/scripts/validate_migration_file_rules.py` validates migration SQL structure.

## License

Apache-2.0
