from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor


@dataclass(frozen=True)
class RecordCountConfig:
    lookback_hours: float
    expected_records: int
    delta_percent: float = 0

    @property
    def minimum_records(self) -> int:
        delta = self.expected_records * self.delta_percent / 100
        return max(0, floor(self.expected_records - delta))

    @property
    def maximum_records(self) -> int:
        delta = self.expected_records * self.delta_percent / 100
        return ceil(self.expected_records + delta)
