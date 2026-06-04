# SQL Object Naming Rules

DDL migrations that create or rename tables, columns, constraints, indexes, or foreign keys must keep database object names consistent across the schema.

## General Convention

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

## Tables

Use plural `snake_case` table names. See `sql-object-naming-examples.md` for good and bad table name examples.

## Columns

Use singular `snake_case` column names. See `sql-object-naming-examples.md` for good and bad column name examples.

## Primary Keys

Primary keys may be named `id` inside each table. For example, the primary key of `users` should be `id`, not `user_id`.

`user_id` is correct when it is a foreign key from another table to `users`.

## Foreign Keys

Foreign keys must use the related table's entity name in singular form plus `_id`:

```text
user_id
product_id
order_id
```

## Timestamps

Timestamp fields that describe when an event happened should preferably end in `_at`:

```text
created_at
updated_at
deleted_at
paid_at
```

## Booleans

Boolean fields must clearly express a true/false condition:

```text
is_active
is_deleted
has_discount
can_login
```

## Join Tables

Simple many-to-many join tables should combine the related plural table names in `snake_case`:

```text
users_roles
products_categories
```

Do not add redundant words such as `has`. The join table already expresses that the relationship exists.

Less recommended names:

```text
users_has_roles
products_has_categories
```

Avoid singular or `camelCase` join table names:

```text
userRole
productCategory
```

Foreign keys inside a join table must use the related entity in singular form plus `_id`:

```text
user_id
role_id
product_id
category_id
```

If the relationship has its own business meaning or stores extra attributes, use a descriptive table name instead of a pure join name.

Good descriptive name:

```text
role_assignments
```

See `many-to-many-table-examples.md` for complete SQL examples.

## Multiple Values

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

## SQL Examples

See `sql-object-naming-examples.md` for complete good and bad SQL examples.
