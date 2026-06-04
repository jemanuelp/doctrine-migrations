# Migration File Examples

## Good DDL Shape

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

## Bad DDL and DML Mix

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

## Good DML Shape With Multiple Inserts

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

## Good DML Shape With One Insert

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
