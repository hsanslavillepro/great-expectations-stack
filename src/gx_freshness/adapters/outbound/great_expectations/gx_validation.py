from __future__ import annotations

from typing import Any

import pandas as pd

from gx_freshness.domain.models.validation_summary import ValidationSummary
from gx_freshness.adapters.outbound.great_expectations.rules import FreshnessValidator, RecordCountValidator


class GreatExpectationsValidationService:
    def validate(self, dataframe: pd.DataFrame) -> ValidationSummary:
        return validate_freshness_frame(dataframe)


def validate_freshness_frame(dataframe: pd.DataFrame) -> ValidationSummary:
    import great_expectations as gx

    context = gx.get_context(mode="ephemeral")
    context.variables.progress_bars = {"globally": False, "metric_calculations": False}

    validator_results = [
        validator.validate(gx, context, dataframe)
        for validator in (
            FreshnessValidator(),
            RecordCountValidator(),
        )
    ]

    raw_result: dict[str, Any] = {}
    for result in validator_results:
        raw_result.update(result.raw_result)

    return ValidationSummary(
        success=all(result.success for result in validator_results),
        checked_tables=len(dataframe.index),
        unexpected_count=sum(result.unexpected_count for result in validator_results),
        raw_result=raw_result,
    )
