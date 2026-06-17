from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pytest

from gx_freshness.adapters.inbound.config import load_config
from gx_freshness.adapters.inbound.cli.database_url_resolver import resolve_database_url
from gx_freshness.adapters.outbound.database import SqlFreshnessRepository
from gx_freshness.adapters.outbound.great_expectations import GreatExpectationsValidationService
from gx_freshness.application import run_freshness_checks


def test_resolve_database_url_uses_explicit_value(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
database_url_env: TEST_DATABASE_URL
schemas:
  - name: main
    defaults:
      freshness_field: updated_at
      freshness_hours: 2
""",
        encoding="utf-8",
    )
    config = load_config(config_path)

    assert resolve_database_url(config, "sqlite://") == "sqlite://"


def test_resolve_database_url_requires_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
database_url_env: TEST_DATABASE_URL
schemas:
  - name: main
    defaults:
      freshness_field: updated_at
      freshness_hours: 2
""",
        encoding="utf-8",
    )
    config = load_config(config_path)

    with pytest.raises(ValueError, match="Database URL"):
        resolve_database_url(config)


def test_run_database_freshness_checks_with_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "freshness.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE orders (updated_at TEXT NOT NULL)")
    connection.execute(
        "INSERT INTO orders VALUES (?)",
        (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f%z"),),
    )
    connection.commit()
    connection.close()

    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
database_url_env: TEST_DATABASE_URL
schemas:
  - name: main
    defaults:
      freshness_field: updated_at
      freshness_hours: 2
      record_count:
        lookback_hours: 1
        expected_records: 1
        delta_percent: 0
""",
        encoding="utf-8",
    )
    config = load_config(config_path)

    result = run_freshness_checks(
        config,
        freshness_repository=SqlFreshnessRepository(f"sqlite:///{db_path}"),
        validation_service=GreatExpectationsValidationService(),
    )

    assert result.success is True
    assert result.validation.checked_tables == 1
    assert result.dataframe.loc[0, "table"] == "orders"
