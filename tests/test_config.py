from pathlib import Path

import pytest

from gx_freshness.adapters.inbound.config import load_config
from gx_freshness.domain import build_table_config


def test_load_config_parses_schema_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
database_url_env: TEST_DATABASE_URL
schemas:
  - name: public
    defaults:
      freshness_field: updated_at
      freshness_hours: 12
      record_count:
        lookback_hours: 1
        expected_records: 100
        delta_percent: 15
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.database_url_env == "TEST_DATABASE_URL"
    assert config.schemas[0].name == "public"
    assert config.schemas[0].defaults.freshness_field == "updated_at"
    assert config.schemas[0].defaults.freshness_hours == 12
    assert config.schemas[0].defaults.record_count is not None
    assert config.schemas[0].defaults.record_count.minimum_records == 85
    assert config.schemas[0].defaults.record_count.maximum_records == 115


def test_build_table_config_applies_table_override(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
schemas:
  - name: public
    defaults:
      freshness_field: updated_at
      freshness_hours: 12
    table_overrides:
      orders:
        freshness_hours: 2
        where: "status = 'ready'"
        record_count:
          lookback_hours: 1
          expected_records: 100
          delta_percent: 10
""",
        encoding="utf-8",
    )

    schema = load_config(config_path).schemas[0]
    table = build_table_config(schema, "orders")

    assert table is not None
    assert table.label == "public.orders"
    assert table.freshness_field == "updated_at"
    assert table.freshness_hours == 2
    assert table.where == "status = 'ready'"
    assert table.record_count is not None
    assert table.record_count.minimum_records == 90


def test_build_table_config_can_disable_table(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
schemas:
  - name: public
    defaults:
      freshness_field: updated_at
      freshness_hours: 12
    table_overrides:
      audit_log:
        enabled: false
""",
        encoding="utf-8",
    )

    schema = load_config(config_path).schemas[0]

    assert build_table_config(schema, "audit_log") is None


def test_load_config_requires_schemas(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text("tables: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="schemas"):
        load_config(config_path)


def test_load_config_rejects_negative_record_count_delta_percent(tmp_path: Path) -> None:
    config_path = tmp_path / "freshness.yml"
    config_path.write_text(
        """
schemas:
  - name: public
    defaults:
      freshness_field: updated_at
      freshness_hours: 2
      record_count:
        lookback_hours: 1
        expected_records: 100
        delta_percent: -1
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="delta_percent"):
        load_config(config_path)
