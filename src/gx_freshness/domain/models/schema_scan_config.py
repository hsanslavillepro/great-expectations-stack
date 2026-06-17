from __future__ import annotations

from dataclasses import dataclass

from gx_freshness.domain.models.table_override_config import TableOverrideConfig
from gx_freshness.domain.models.table_rule_config import TableRuleConfig


@dataclass(frozen=True)
class SchemaScanConfig:
    name: str
    defaults: TableRuleConfig
    table_overrides: dict[str, TableOverrideConfig]
