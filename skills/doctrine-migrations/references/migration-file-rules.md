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

## SQL Object Naming

DDL migrations that create or rename tables, columns, constraints, indexes, or foreign keys must keep database object names consistent across the schema.

General convention:

- Use one naming convention everywhere in the database.
- Prefer `snake_case` for SQL table and column names.
- Use plural table names because tables represent collections of rows.
- Use singular column names because columns represent one value per row.
- Avoid `camelCase`, `PascalCase`, and mixed-case SQL identifiers.
- Avoid reserved words, ambiguous names, and overly generic names.
- Use clear, descriptive names that explain the stored data without relying on hidden context.

Recommended shape:

```text
Tables: plural + snake_case
Columns: singular + snake_case
Primary key: id
Foreign key: singular_related_table_name_id
```

Good table names:

```text
users
products
orders
order_items
user_addresses
users_roles
products_categories
```

Bad table names:

```text
user
product
order
orderItems
userAddresses
userRole
productCategory
```

Good column names:

```text
id
email
phone_number
status
first_name
total_amount
payment_status
unit_price
created_at
updated_at
deleted_at
paid_at
is_active
is_deleted
has_discount
can_login
user_id
product_id
order_id
```

Bad column names:

```text
UserId
emails
phoneNumbers
statuses
firstName
totalAmount
creationDate
updateDate
active
deleted
users_id
products_id
orders_id
date
type
amount
status2
price1
```

Primary keys may be named `id` inside each table. For example, the primary key of `users` should be `id`, not `user_id`. `user_id` is correct when it is a foreign key from another table to `users`.

Foreign keys must use the related table's entity name in singular form plus `_id`:

```text
user_id
product_id
order_id
```

Timestamp fields that describe when an event happened should preferably end in `_at`:

```text
created_at
updated_at
deleted_at
paid_at
```

Boolean fields must clearly express a true/false condition:

```text
is_active
is_deleted
has_discount
can_login
```

Many-to-many join tables should combine the related plural table names in `snake_case`:

```text
users_roles
products_categories
```

Do not store multiple values in one field. If one row can have multiple values, model them with a related table.

Bad structure:

```text
users
- id
- name
- emails
```

Good structure:

```text
users
- id
- name

user_emails
- id
- user_id
- email
```

Good SQL example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    unit_price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    paid_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
);

CREATE TABLE order_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(id),

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
);
```

Bad SQL example:

```sql
CREATE TABLE User (
    UserId BIGINT PRIMARY KEY,
    firstName VARCHAR(100) NOT NULL,
    lastName VARCHAR(100),
    emails VARCHAR(255),
    active BOOLEAN DEFAULT true,
    creationDate TIMESTAMP NOT NULL
);

CREATE TABLE Product (
    ProductId BIGINT PRIMARY KEY,
    productName VARCHAR(150) NOT NULL,
    price1 DECIMAL(10, 2) NOT NULL,
    active BOOLEAN DEFAULT true
);

CREATE TABLE Order (
    OrderId BIGINT PRIMARY KEY,
    users_id BIGINT NOT NULL,
    status2 VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    date TIMESTAMP NOT NULL
);

CREATE TABLE orderItems (
    OrderItemId BIGINT PRIMARY KEY,
    OrdersId BIGINT NOT NULL,
    ProductsId BIGINT NOT NULL,
    qty INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
```

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
