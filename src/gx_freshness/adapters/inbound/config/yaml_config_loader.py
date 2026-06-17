from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from gx_freshness.domain.models.freshness_config import FreshnessConfig
from gx_freshness.domain.models.record_count_config import RecordCountConfig
from gx_freshness.domain.models.schema_scan_config import SchemaScanConfig
from gx_freshness.domain.models.table_override_config import TableOverrideConfig
from gx_freshness.domain.models.table_rule_config import TableRuleConfig


def load_config(path: str | Path) -> FreshnessConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a YAML mapping.")

    schema_entries = raw.get("schemas")
    if not isinstance(schema_entries, list) or not schema_entries:
        raise ValueError("Config must define a non-empty 'schemas' list.")

    return FreshnessConfig(
        schemas=tuple(_parse_schema(entry, index) for index, entry in enumerate(schema_entries, start=1)),
        database_url_env=str(raw.get("database_url_env", "DATABASE_URL")),
    )


def _parse_schema(raw: Any, index: int) -> SchemaScanConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"schemas[{index}] must be a mapping.")

    name = _required_string(raw, "name", f"schemas[{index}]")
    defaults = _parse_rule(raw.get("defaults"), f"schemas[{index}].defaults")
    overrides = _parse_table_overrides(raw.get("table_overrides", {}), f"schemas[{index}].table_overrides")

    return SchemaScanConfig(
        name=name,
        defaults=defaults,
        table_overrides=overrides,
    )


def _parse_rule(raw: Any, label: str) -> TableRuleConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a mapping.")

    return TableRuleConfig(
        freshness_field=_required_string(raw, "freshness_field", label),
        freshness_hours=_positive_float(raw.get("freshness_hours"), f"{label}.freshness_hours"),
        where=_optional_string(raw.get("where")),
        record_count=_parse_record_count(raw.get("record_count"), f"{label}.record_count"),
    )


def _parse_table_overrides(raw: Any, label: str) -> dict[str, TableOverrideConfig]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a mapping.")

    return {
        str(table_name): _parse_table_override(override_raw, f"{label}.{table_name}")
        for table_name, override_raw in raw.items()
    }


def _parse_table_override(raw: Any, label: str) -> TableOverrideConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a mapping.")

    freshness_hours = raw.get("freshness_hours")
    return TableOverrideConfig(
        enabled=bool(raw.get("enabled", True)),
        freshness_field=_optional_string(raw.get("freshness_field")),
        freshness_hours=_positive_float(freshness_hours, f"{label}.freshness_hours")
        if freshness_hours is not None
        else None,
        where=_optional_string(raw.get("where")),
        record_count=_parse_record_count(raw.get("record_count"), f"{label}.record_count"),
    )


def _parse_record_count(raw: Any, label: str) -> RecordCountConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must be a mapping.")

    return RecordCountConfig(
        lookback_hours=_positive_float(raw.get("lookback_hours"), f"{label}.lookback_hours"),
        expected_records=_non_negative_int(raw.get("expected_records"), f"{label}.expected_records"),
        delta_percent=_non_negative_float(raw.get("delta_percent", 0), f"{label}.delta_percent"),
    )


def _required_string(raw: dict[str, Any], key: str, label: str) -> str:
    value = _optional_string(raw.get(key))
    if value is None:
        raise ValueError(f"{label}.{key} is required.")
    return value


def _positive_float(value: Any, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number.") from exc

    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return parsed


def _non_negative_int(value: Any, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer.") from exc

    if parsed < 0:
        raise ValueError(f"{label} must be greater than or equal to zero.")
    return parsed


def _non_negative_float(value: Any, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number.") from exc

    if parsed < 0:
        raise ValueError(f"{label} must be greater than or equal to zero.")
    return parsed


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    parsed = str(value).strip()
    return parsed or None
