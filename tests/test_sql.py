from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

from gx_freshness.adapters.outbound.database import (
    build_latest_value_query,
    build_record_count_query,
    check_table_freshness,
    discover_tables,
)
from gx_freshness.domain import RecordCountConfig, SchemaScanConfig, TableFreshnessConfig, TableRuleConfig


def test_build_latest_value_query_quotes_identifiers() -> None:
    engine = create_engine("sqlite://")
    table = TableFreshnessConfig(
        schema="analytics",
        name="orders",
        freshness_field="updated_at",
        freshness_hours=2,
    )

    assert build_latest_value_query(engine, table) == (
        "SELECT MAX(updated_at) AS latest_value FROM analytics.orders"
    )


def test_build_record_count_query_uses_lookback_cutoff() -> None:
    engine = create_engine("sqlite://")
    table = TableFreshnessConfig(
        schema="analytics",
        name="orders",
        freshness_field="updated_at",
        freshness_hours=2,
        where="status = 'ready'",
        record_count=RecordCountConfig(
            lookback_hours=1,
            expected_records=10,
            delta_percent=20,
        ),
    )

    assert build_record_count_query(engine, table) == (
        "SELECT COUNT(*) AS actual_record_count FROM analytics.orders "
        "WHERE (status = 'ready') AND updated_at >= :record_count_cutoff"
    )


def test_check_table_freshness_for_fresh_sqlite_table() -> None:
    engine = create_engine("sqlite://")
    latest = datetime.now(timezone.utc) - timedelta(minutes=30)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE orders (updated_at TEXT NOT NULL)"))
        connection.execute(
            text("INSERT INTO orders (updated_at) VALUES (:updated_at)"),
            {"updated_at": latest.isoformat()},
        )

    result = check_table_freshness(
        engine,
        TableFreshnessConfig(
            schema="main",
            name="orders",
            freshness_field="updated_at",
            freshness_hours=2,
        ),
    )

    assert result.error is None
    assert result.is_fresh is True
    assert result.age_hours is not None
    assert result.age_hours < 1


def test_check_table_freshness_counts_recent_records_with_percentage_tolerance() -> None:
    engine = create_engine("sqlite://")
    now = datetime.now(timezone.utc)
    timestamp_format = "%Y-%m-%d %H:%M:%S.%f%z"
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE orders (updated_at TEXT NOT NULL)"))
        connection.execute(
            text("INSERT INTO orders (updated_at) VALUES (:updated_at)"),
            [
                {"updated_at": (now - timedelta(minutes=20)).strftime(timestamp_format)},
                {"updated_at": (now - timedelta(minutes=40)).strftime(timestamp_format)},
                {"updated_at": (now - timedelta(hours=3)).strftime(timestamp_format)},
            ],
        )

    result = check_table_freshness(
        engine,
        TableFreshnessConfig(
            schema="main",
            name="orders",
            freshness_field="updated_at",
            freshness_hours=4,
            record_count=RecordCountConfig(
                lookback_hours=1,
                expected_records=3,
                delta_percent=34,
            ),
        ),
    )

    assert result.error is None
    assert result.actual_record_count == 2
    assert result.record_count_minimum == 1
    assert result.record_count_maximum == 5
    assert result.is_record_count_valid is True


def test_discover_tables_expands_schema_scan_defaults() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE orders (updated_at TEXT NOT NULL)"))
        connection.execute(text("CREATE TABLE audit_log (updated_at TEXT NOT NULL)"))

    tables = discover_tables(
        engine,
        (
            SchemaScanConfig(
                name="main",
                defaults=TableRuleConfig(
                    freshness_field="updated_at",
                    freshness_hours=2,
                ),
                table_overrides={},
            ),
        ),
    )

    assert [table.label for table in tables] == ["main.audit_log", "main.orders"]
