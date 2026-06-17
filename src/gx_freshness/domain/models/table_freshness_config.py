from __future__ import annotations

from dataclasses import dataclass

from gx_freshness.domain.models.record_count_config import RecordCountConfig


@dataclass(frozen=True)
class TableFreshnessConfig:
    schema: str
    name: str
    freshness_field: str
    freshness_hours: float
    where: str | None = None
    record_count: RecordCountConfig | None = None

    @property
    def label(self) -> str:
        return f"{self.schema}.{self.name}"
