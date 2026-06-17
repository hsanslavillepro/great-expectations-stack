from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from gx_freshness.domain.models.validation_summary import ValidationSummary


@dataclass(frozen=True)
class FreshnessRunResult:
    success: bool
    dataframe: pd.DataFrame
    validation: ValidationSummary
