from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from gx_freshness.domain import SchemaScanConfig, TableFreshnessConfig, build_table_config

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FreshnessRow:
    table: str
    schema: str | None
    freshness_field: str
    expected_hours: float
    latest_value: datetime | None
    age_hours: float | None
    freshness_margin_hours: float | None
    is_fresh: bool
    record_count_lookback_hours: float | None = None
    expected_record_count: int | None = None
    record_count_delta_percent: float | None = None
    record_count_minimum: int | None = None
    record_count_maximum: int | None = None
    actual_record_count: int | None = None
    is_record_count_valid: bool | None = None
    error: str | None = None


class SqlFreshnessRepository:
    def __init__(self, database_url: str) -> None:
        self.engine = make_engine(database_url)

    def collect_freshness(self, schemas: tuple[SchemaScanConfig, ...]) -> pd.DataFrame:
        tables = discover_tables(self.engine, schemas)
        logger.info("Discovered %s table(s) to validate", len(tables))
        return collect_freshness(self.engine, tables)


def make_engine(database_url: str) -> Engine:
    logger.info("Creating SQLAlchemy engine")
    return create_engine(database_url)


def collect_freshness(engine: Engine, tables: tuple[TableFreshnessConfig, ...]) -> pd.DataFrame:
    logger.info("Collecting freshness metrics for %s table(s)", len(tables))
    rows = [check_table_freshness(engine, table) for table in tables]
    return pd.DataFrame([row.__dict__ for row in rows])


def discover_tables(engine: Engine, schemas: tuple[SchemaScanConfig, ...]) -> tuple[TableFreshnessConfig, ...]:
    inspector = inspect(engine)
    tables: list[TableFreshnessConfig] = []

    for schema in schemas:
        logger.info("Discovering tables in schema %s", schema.name)
        # Schema scans expand configured defaults into one table check per discovered table.
        for table_name in sorted(inspector.get_table_names(schema=schema.name)):
            table = build_table_config(schema, table_name)
            if table is not None:
                logger.info("Discovered table %s", table.label)
                tables.append(table)
            else:
                logger.info("Skipping disabled table %s.%s", schema.name, table_name)

    if not tables:
        raise ValueError("No tables were discovered from configured schemas.")

    return tuple(tables)


def check_table_freshness(engine: Engine, table: TableFreshnessConfig) -> FreshnessRow:
    logger.info("Checking table %s", table.label)
    try:
        latest_value = _fetch_latest_value(engine, table)
        age_hours = _age_in_hours(latest_value)
        margin = None if age_hours is None else table.freshness_hours - age_hours
        record_count_values = _record_count_values(engine, table)
        logger.info(
            "Finished table %s freshness_ok=%s record_count_ok=%s",
            table.label,
            bool(margin is not None and margin >= 0),
            record_count_values["is_record_count_valid"],
        )
        return FreshnessRow(
            table=table.name,
            schema=table.schema,
            freshness_field=table.freshness_field,
            expected_hours=table.freshness_hours,
            latest_value=latest_value,
            age_hours=age_hours,
            freshness_margin_hours=margin,
            is_fresh=bool(margin is not None and margin >= 0),
            **record_count_values,
        )
    except Exception as exc:  # noqa: BLE001 - each table should report its own failure.
        logger.error("Failed to check table %s: %s", table.label, exc)
        logger.debug("Table check traceback for %s", table.label, exc_info=True)
        return FreshnessRow(
            table=table.name,
            schema=table.schema,
            freshness_field=table.freshness_field,
            expected_hours=table.freshness_hours,
            latest_value=None,
            age_hours=None,
            freshness_margin_hours=None,
            is_fresh=False,
            **_empty_record_count_values(table),
            error=str(exc),
        )


def build_latest_value_query(engine: Engine, table: TableFreshnessConfig) -> str:
    preparer = engine.dialect.identifier_preparer
    field = _quote_identifier(preparer, table.freshness_field)
    table_name = _qualified_table_name(preparer, table)

    # Freshness is measured from the newest value in the configured timestamp column.
    query = f"SELECT MAX({field}) AS latest_value FROM {table_name}"
    if table.where:
        query = f"{query} WHERE {table.where}"
    return query


def build_record_count_query(engine: Engine, table: TableFreshnessConfig) -> str:
    preparer = engine.dialect.identifier_preparer
    field = _quote_identifier(preparer, table.freshness_field)
    table_name = _qualified_table_name(preparer, table)
    # The cutoff value is bound as a parameter because it changes every run.
    predicates = [f"{field} >= :record_count_cutoff"]
    if table.where:
        predicates.insert(0, f"({table.where})")

    return f"SELECT COUNT(*) AS actual_record_count FROM {table_name} WHERE {' AND '.join(predicates)}"


def _fetch_latest_value(engine: Engine, table: TableFreshnessConfig) -> datetime | None:
    query = build_latest_value_query(engine, table)
    logger.debug("Latest value SQL for %s: %s", table.label, query)
    with engine.connect() as connection:
        value = connection.execute(text(query)).scalar_one_or_none()
    return _coerce_datetime(value)


def _record_count_values(engine: Engine, table: TableFreshnessConfig) -> dict[str, Any]:
    if table.record_count is None:
        return _empty_record_count_values(table)

    # Count only records inserted within the configured rolling lookback window.
    cutoff = datetime.now(timezone.utc) - timedelta(hours=table.record_count.lookback_hours)
    query = build_record_count_query(engine, table)
    cutoff_value = _record_count_cutoff_value(engine, cutoff)
    logger.debug("Record count SQL for %s: %s", table.label, query)
    logger.debug("Record count params for %s: record_count_cutoff=%s", table.label, cutoff_value)
    with engine.connect() as connection:
        actual_count = int(
            connection.execute(
                text(query),
                {"record_count_cutoff": cutoff_value},
            ).scalar_one()
        )

    minimum = table.record_count.minimum_records
    maximum = table.record_count.maximum_records
    return {
        "record_count_lookback_hours": table.record_count.lookback_hours,
        "expected_record_count": table.record_count.expected_records,
        "record_count_delta_percent": table.record_count.delta_percent,
        "record_count_minimum": minimum,
        "record_count_maximum": maximum,
        "actual_record_count": actual_count,
        "is_record_count_valid": minimum <= actual_count <= maximum,
    }


def _empty_record_count_values(table: TableFreshnessConfig) -> dict[str, Any]:
    if table.record_count is None:
        return {
            "record_count_lookback_hours": None,
            "expected_record_count": None,
            "record_count_delta_percent": None,
            "record_count_minimum": None,
            "record_count_maximum": None,
            "actual_record_count": None,
            "is_record_count_valid": None,
        }

    return {
        "record_count_lookback_hours": table.record_count.lookback_hours,
        "expected_record_count": table.record_count.expected_records,
        "record_count_delta_percent": table.record_count.delta_percent,
        "record_count_minimum": table.record_count.minimum_records,
        "record_count_maximum": table.record_count.maximum_records,
        "actual_record_count": None,
        "is_record_count_valid": False,
    }


def _record_count_cutoff_value(engine: Engine, cutoff: datetime) -> datetime | str:
    if engine.dialect.name == "sqlite":
        return cutoff.strftime("%Y-%m-%d %H:%M:%S.%f%z")
    return cutoff


def _qualified_table_name(preparer: Any, table: TableFreshnessConfig) -> str:
    table_name = _quote_identifier(preparer, table.name)
    if table.schema:
        table_name = f"{_quote_identifier(preparer, table.schema)}.{table_name}"
    return table_name


def _quote_identifier(preparer: Any, value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return preparer.quote(value)


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        parsed = pd.to_datetime(value, utc=False, errors="raise")
        return parsed.to_pydatetime()
    raise TypeError(f"Expected datetime-compatible freshness value, got {type(value).__name__}.")


def _age_in_hours(value: datetime | None) -> float | None:
    if value is None:
        return None

    now = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return (now - value).total_seconds() / 3600
