from __future__ import annotations

from dataclasses import dataclass

from gx_freshness.domain.models.schema_scan_config import SchemaScanConfig


@dataclass(frozen=True)
class FreshnessConfig:
    schemas: tuple[SchemaScanConfig, ...]
    database_url_env: str = "DATABASE_URL"
