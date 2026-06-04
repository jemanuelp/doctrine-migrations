# SQL Object Naming SQL Examples

## Good SQL Example

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

## Bad SQL Example

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
