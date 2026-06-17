from __future__ import annotations

import json
import logging
import sys
from typing import TextIO

from gx_freshness.domain.models.freshness_run_result import FreshnessRunResult

logger = logging.getLogger(__name__)


class FreshnessResultRenderer:
    table_columns = [
        "schema",
        "table",
        "freshness_field",
        "latest_value",
        "age_hours",
        "expected_hours",
        "freshness_margin_hours",
        "is_fresh",
        "record_count_lookback_hours",
        "expected_record_count",
        "record_count_delta_percent",
        "actual_record_count",
        "record_count_minimum",
        "record_count_maximum",
        "is_record_count_valid",
        "error",
    ]

    def __init__(self, output: TextIO = sys.stdout) -> None:
        self.output = output

    def render(self, result: FreshnessRunResult, json_output: bool) -> None:
        if json_output:
            self.render_json(result)
        else:
            self.render_table(result)

    def render_json(self, result: FreshnessRunResult) -> None:
        self.output.write(json.dumps(self.json_payload(result), default=str, indent=2) + "\n")

    def render_table(self, result: FreshnessRunResult) -> None:
        logger.info("\n%s", result.dataframe[self.table_columns].to_string(index=False))
        logger.info(
            "GX validation success=%s checked_tables=%s unexpected_count=%s",
            result.validation.success,
            result.validation.checked_tables,
            result.validation.unexpected_count,
        )

    def json_payload(self, result: FreshnessRunResult) -> dict[str, object]:
        return {
            "success": result.success,
            "tables": result.dataframe.where(result.dataframe.notna(), None).to_dict(orient="records"),
            "validation": {
                "success": result.validation.success,
                "checked_tables": result.validation.checked_tables,
                "unexpected_count": result.validation.unexpected_count,
            },
        }
