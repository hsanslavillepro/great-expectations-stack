# GX Freshness

YAML-driven data freshness checks using Great Expectations.

The CLI reads a YAML file containing schemas to scan plus default freshness rules. It discovers every table in each schema, runs one query per table, computes how old the newest timestamp is, then validates the result dataframe with Great Expectations.

## Install

Using `uv`:

```bash
make deps
```

Run commands through the local environment:

```bash
.venv/bin/gx-freshness --help
.venv/bin/pytest
```

Or use `make`:

```bash
make deps-dev
make test
```

For CI:

```bash
make deps-tests
make test-coverage
```

For Hive Kerberos integration tests:

```bash
make deps-hive-tests
source .env.hive.example
make test-hive
```

The Hive connection uses a Kerberos ticket that already exists. Pass the ticket
cache path with `KRB5CCNAME`, for example `FILE:/tmp/krb5cc_my_user`, and pass
the Hive SQLAlchemy URL with `DATABASE_URL`:

```bash
export KRB5CCNAME='FILE:/tmp/krb5cc_my_user'
export DATABASE_URL='hive://my_user@hive-server.example.com:10000/default?auth=KERBEROS&kerberos_service_name=hive'
gx-freshness run --config configs/freshness.hive-kerberos.example.yml
```

Refresh the lock files after dependency changes:

```bash
make lock
```

For pip-compatible environments:

```bash
python -m venv .venv
source .venv/bin/activate
uv pip install -r requirements/app.dependencies.txt -r requirements/postgres.dependencies.txt -r requirements/test.dependencies.txt
uv pip install --no-deps -e .
```

For non-Postgres databases, install the SQLAlchemy driver for your database and use the matching database URL.

## Configure

Copy `configs/freshness.example.yml` and adjust it:

```yaml
database_url_env: DATABASE_URL
schemas:
  - name: public
    defaults:
      freshness_field: updated_at
      freshness_hours: 24
      record_count:
        lookback_hours: 1
        expected_records: 100
        delta_percent: 10
    table_overrides:
      orders:
        freshness_hours: 6
      audit_log:
        enabled: false

  - name: mart
    defaults:
      freshness_field: loaded_at
      freshness_hours: 25
      where: "business_date >= CURRENT_DATE - INTERVAL '3 days'"
```

`freshness_field` is the parametrized field used by the query:

```sql
SELECT MAX(<freshness_field>) AS latest_value
FROM <schema>.<table>
```

`record_count` is optional. When configured, the CLI counts records where `freshness_field` is within the last `lookback_hours` and validates that the count is within `delta_percent` of `expected_records`.

Rules under `defaults` apply to every discovered table in the schema. Use `table_overrides` to change a rule for one table or set `enabled: false` to skip that table.

## Run

```bash
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/dbname"
gx-freshness run --config configs/freshness.example.yml
```

You can also pass a database URL directly:

```bash
gx-freshness run --config configs/freshness.example.yml --database-url "$DATABASE_URL"
```

The process exits with `0` when all tables are fresh and `1` when any table is stale or cannot be checked.

To avoid committing secrets, keep the real database URL in a local `.env` file. The `.env` file is ignored by Git; only `.env.example` is committed as a template.

```bash
cp .env.example .env
set -a
source .env
set +a
gx-freshness run --config configs/freshness.example.yml
```

## Output

By default, the CLI prints a compact table and a Great Expectations validation summary. Add `--json` for machine-readable output.

## Local Postgres Demo

Start Postgres and run the Flyway migration:

```bash
docker compose up -d
```

The compose stack creates a `gx_freshness` database and Flyway creates two schemas:

- `validation_core`
- `validation_mart`

Each schema contains two tables, and each table has an `insert_date_time` column for freshness validation:

- `validation_core.orders`
- `validation_core.customers`
- `validation_mart.daily_sales`
- `validation_mart.inventory_snapshot`

Run the freshness validation against the local database:

```bash
cp .env.example .env
set -a
source .env
set +a
gx-freshness run --config configs/freshness.local-postgres.yml
```

Or with `make`:

```bash
cp .env.example .env
make docker-up
make run-local-postgres
```

For JSON output:

```bash
gx-freshness run --config configs/freshness.local-postgres.yml --json
```

Show SQL queries and debug details:

```bash
gx-freshness run --config configs/freshness.local-postgres.yml --log-level DEBUG
```

You can also set the log level with an environment variable:

```bash
export GX_FRESHNESS_LOG_LEVEL=DEBUG
gx-freshness run --config configs/freshness.local-postgres.yml
```

Flyway seeds timestamps relative to `NOW()` only when the migration first runs. If the demo data becomes stale later, reset the local database with:

```bash
docker compose down -v
docker compose up -d
```
