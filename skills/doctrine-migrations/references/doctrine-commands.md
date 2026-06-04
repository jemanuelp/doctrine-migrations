# Doctrine Commands Through `migrations.sh`

Run every Doctrine migrations command from the `migrations/` directory:

```bash
cd migrations
./migrations.sh <command> [args] [options]
```

The wrapper forwards all arguments to `./vendor/bin/doctrine-migrations`. Prefer canonical `migrations:*` names.

## General Console Commands

| Command | Purpose | Example |
| --- | --- | --- |
| `completion` | Dump shell completion script. | `./migrations.sh completion bash` |
| `help` | Show command help. | `./migrations.sh help migrations:migrate` |
| `list` | List available console commands. | `./migrations.sh list` |

## Status and Inspection

| Command | Purpose | Example |
| --- | --- | --- |
| `migrations:status` | Show migration storage, counts, and current state. | `./migrations.sh migrations:status` |
| `migrations:list` | List available migrations and execution status. | `./migrations.sh migrations:list` |
| `migrations:current` | Output the current executed version. | `./migrations.sh migrations:current` |
| `migrations:latest` | Output the latest available version. | `./migrations.sh migrations:latest` |
| `migrations:up-to-date` | Check if all migrations are applied. | `./migrations.sh migrations:up-to-date` |

## Creation and Schema Capture

| Command | Purpose | Example |
| --- | --- | --- |
| `migrations:generate` | Generate a blank migration class. | `./migrations.sh migrations:generate` |
| `migrations:diff` | Generate a migration from DB vs ORM metadata diff. | `./migrations.sh migrations:diff` |
| `migrations:dump-schema` | Dump current DB schema into a migration. | `./migrations.sh migrations:dump-schema` |

## Execution

| Command | Purpose | Example |
| --- | --- | --- |
| `migrations:migrate` | Apply migrations to latest or a target version. | `./migrations.sh migrations:migrate` |
| `migrations:migrate <version>` | Migrate to a specific version. | `./migrations.sh migrations:migrate 20260429173000` |
| `migrations:execute` | Execute a version manually up or down. | `./migrations.sh migrations:execute --up 'Migrations\\Version20260429173000'` |
| `migrations:execute --down` | Roll back one version manually; destructive. | `./migrations.sh migrations:execute --down 'Migrations\\Version20260429173000'` |

## Metadata Management

| Command | Purpose | Example |
| --- | --- | --- |
| `migrations:sync-metadata-storage` | Ensure metadata storage schema is up to date. | `./migrations.sh migrations:sync-metadata-storage` |
| `migrations:version` | Manually add/delete versions in metadata. | `./migrations.sh migrations:version --add 'Migrations\\Version20260429173000'` |
| `migrations:rollup` | Delete tracked versions and mark one version as current; destructive. | `./migrations.sh migrations:rollup` |

## Safe Workflow Recipes

### Inspect before work

```bash
cd migrations
./migrations.sh migrations:status
./migrations.sh migrations:list
```

### Create a manual migration

```bash
cd migrations
./migrations.sh migrations:generate
```

Then edit the generated file under `migrations/migrations/` and write explicit SQL in `up()` and `down()`.

### Generate from entity metadata

```bash
cd migrations
./migrations.sh migrations:diff
```

Before running this, verify related NestJS entities are present in `api/src/database/entities.ts`.

### Apply locally

```bash
cd migrations
./migrations.sh migrations:status
./migrations.sh migrations:migrate
./migrations.sh migrations:status
```

### Roll back manually

Ask for explicit confirmation first, then run:

```bash
cd migrations
./migrations.sh migrations:execute --down 'Migrations\\VersionYYYYMMDDHHMMSS'
```
