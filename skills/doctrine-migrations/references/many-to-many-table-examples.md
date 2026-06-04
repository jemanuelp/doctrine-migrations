# Many-to-Many Table Examples

## Recommended SQL

```sql
CREATE TABLE users_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,

    PRIMARY KEY (user_id, role_id),

    CONSTRAINT fk_users_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT fk_users_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
);

CREATE TABLE products_categories (
    product_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,

    PRIMARY KEY (product_id, category_id),

    CONSTRAINT fk_products_categories_product
        FOREIGN KEY (product_id)
        REFERENCES products(id),

    CONSTRAINT fk_products_categories_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
);
```

## Less Recommended SQL

```sql
CREATE TABLE users_has_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL
);

CREATE TABLE products_has_categories (
    product_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL
);
```

## Bad SQL

```sql
CREATE TABLE userRole (
    users_id BIGINT NOT NULL,
    roles_id BIGINT NOT NULL
);

CREATE TABLE productCategory (
    products_id BIGINT NOT NULL,
    categories_id BIGINT NOT NULL
);
```

## Relationship With Its Own Meaning

Use a descriptive table name when the relationship stores additional attributes or has its own business meaning.

```sql
CREATE TABLE role_assignments (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_role_assignments_user
        FOREIGN KEY (user_id)
        REFERENCES users(id),

    CONSTRAINT fk_role_assignments_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
);
```
