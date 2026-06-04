# Migration File Rules

## Core Rule

Migration files must be either DDL-only or DML-only. Never mix schema changes and data changes in the same migration version.

## File and Class Naming

After creating a migration with `sh migrations.sh generate`, rename the generated file and class.

Required shape:

- Prefix: `VersionYYYYMMDDHHMMSS` from the generated migration timestamp.
- Suffix: English `snake_case` describing the change.
- File name: `VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php`.
- Class name: exactly the same as the file stem.

Good names:

```text
Version20250325180154_add_integration_column_to_instance_table.php
Version20250108163808_create_message_context_info_table.php
Version20250319164423_alter_media_data_drop_not_null_disappearing_mode_initiator.php
```

Good class declaration:

```php
final class Version20250325180154_add_integration_column_to_instance_table extends AbstractMigration
```

Bad names:

```text
Version20250325180154.php
Version20250325180154AddIntegrationColumnToInstanceTable.php
```

Bad class declaration:

```php
final class Version20250325180154AddIntegrationColumnToInstanceTable extends AbstractMigration
```

Fix bad names by preserving the `VersionYYYYMMDDHHMMSS` prefix and adding an English snake_case suffix. Then update the internal class name to match the renamed file.

## DDL Migrations

DDL statements change schema: `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `CREATE INDEX`, `DROP INDEX`, constraints, foreign keys, and similar structural operations.

For DDL:

- Create one migration file per DDL statement.
- `up()` must contain exactly one `$this->addSql(...)` call.
- `down()` must contain exactly one `$this->addSql(...)` call.
- If a generated diff contains multiple DDL statements, split it into multiple migration files.
- If schema creation needs seed/default data, put the DML in a later data migration.

Good DDL shape:

```php
final class Version20241210163340_create_branch_table extends AbstractMigration
{
    public function getDescription(): string
    {
        return '';
    }

    public function up(Schema $schema): void
    {
        $this->addSql('
            CREATE TABLE "branch" (
                id serial2 NOT NULL,
                name varchar(100) NOT NULL,
                CONSTRAINT branch_pk PRIMARY KEY (id)
            );
        ');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE "branch";');
    }
}
```

Bad DDL + DML mix:

```php
public function up(Schema $schema): void
{
    $this->addSql('CREATE TABLE "template" (...);');
    $this->addSql('INSERT INTO "template" (...) VALUES (...);');
}

public function down(Schema $schema): void
{
    $this->addSql('DROP TABLE "template";');
    $this->addSql('DELETE FROM "template" WHERE ...;');
}
```

Fix the bad shape by creating two files: one DDL migration for the table and one DML migration for the default row.

## DML Migrations

DML statements change data: `INSERT`, `UPDATE`, `DELETE`, and data backfills.

For DML:

- Multiple `$this->addSql(...)` calls are allowed in `up()`.
- Multiple `$this->addSql(...)` calls are allowed in `down()`.
- Keep related data changes together when they form one logical seed/backfill.
- Write deterministic rollback SQL whenever possible.

Good DML shape with multiple inserts:

```php
final class Version20241210163341_create_branch_table extends AbstractMigration
{
    public function getDescription(): string
    {
        return '';
    }

    public function up(Schema $schema): void
    {
        $this->addSql("INSERT INTO branch (id, name) VALUES (1, 'Argentina');");
        $this->addSql("INSERT INTO branch (id, name) VALUES (2, 'Colombia');");
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DELETE FROM branch WHERE id IN (1, 2);');
    }
}
```

Good DML shape with one insert:

```php
final class Version20250521214458_insert_origin_types_data extends AbstractMigration
{
    public function getDescription(): string
    {
        return '';
    }

    public function up(Schema $schema): void
    {
        $this->addSql("INSERT INTO origin_types (id, origin_type) VALUES (1, 'INBOUND');");
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DELETE FROM origin_types WHERE id = 1;');
    }
}
```

## Review Checklist

- File name matches `VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php`.
- Internal class name exactly matches the file stem.
- The migration is DDL-only or DML-only.
- DDL files contain exactly one `addSql` in `up()` and one in `down()`.
- DML files may contain multiple `addSql` calls, but all statements belong to one logical data change.
- DDL and DML are split into ordered migration versions.
- `down()` reverses the exact effect of `up()` where feasible.

## Automated Enforcement

Run the naming-only validator from the repo root:

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py migrations/migrations
```

Validate one file's name and class while authoring a new migration:

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_names.py migrations/migrations/VersionYYYYMMDDHHMMSS_name.php
```

Run the full file-rule validator from the repo root:

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py migrations/migrations
```

Validate one file while authoring a new migration:

```bash
python3 .agents/skills/doctrine-migrations/scripts/validate_migration_file_rules.py migrations/migrations/VersionYYYYMMDDHHMMSS_name.php
```

The validator fails when:

- A file mixes DDL and DML statements.
- A file is still named only `VersionYYYYMMDDHHMMSS.php`.
- A file or class uses camelCase/PascalCase suffix instead of English snake_case.
- The internal class name does not match the file stem.
- A DDL migration has more or fewer than one `addSql` call in `up()`.
- A DDL migration has more or fewer than one `addSql` call in `down()`.
- A DDL migration has more or fewer than one DDL statement in either method.
- A SQL statement cannot be classified as DDL or DML.
