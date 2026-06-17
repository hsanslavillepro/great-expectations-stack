from __future__ import annotations

from dataclasses import replace

from gx_freshness.domain.models.schema_scan_config import SchemaScanConfig
from gx_freshness.domain.models.table_freshness_config import TableFreshnessConfig


def build_table_config(schema: SchemaScanConfig, table_name: str) -> TableFreshnessConfig | None:
    override = schema.table_overrides.get(table_name)
    if override and not override.enabled:
        return None

    rule = schema.defaults
    if override:
        rule = replace(
            rule,
            freshness_field=override.freshness_field or rule.freshness_field,
            freshness_hours=override.freshness_hours
            if override.freshness_hours is not None
            else rule.freshness_hours,
            where=override.where if override.where is not None else rule.where,
            record_count=override.record_count if override.record_count is not None else rule.record_count,
        )

    return TableFreshnessConfig(
        schema=schema.name,
        name=table_name,
        freshness_field=rule.freshness_field,
        freshness_hours=rule.freshness_hours,
        where=rule.where,
        record_count=rule.record_count,
    )
