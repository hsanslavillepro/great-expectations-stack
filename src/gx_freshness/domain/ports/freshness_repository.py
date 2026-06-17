from __future__ import annotations

from typing import Protocol

import pandas as pd

from gx_freshness.domain.models.schema_scan_config import SchemaScanConfig


class FreshnessRepository(Protocol):
    def collect_freshness(self, schemas: tuple[SchemaScanConfig, ...]) -> pd.DataFrame:
        raise NotImplementedError
