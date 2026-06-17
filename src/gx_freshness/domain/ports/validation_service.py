from __future__ import annotations

from typing import Protocol

import pandas as pd

from gx_freshness.domain.models.validation_summary import ValidationSummary


class ValidationService(Protocol):
    def validate(self, dataframe: pd.DataFrame) -> ValidationSummary:
        raise NotImplementedError
