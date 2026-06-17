from __future__ import annotations

from dataclasses import dataclass

from gx_freshness.domain.models.record_count_config import RecordCountConfig


@dataclass(frozen=True)
class TableOverrideConfig:
    enabled: bool = True
    freshness_field: str | None = None
    freshness_hours: float | None = None
    where: str | None = None
    record_count: RecordCountConfig | None = None
