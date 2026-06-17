from __future__ import annotations

from typing import Any

from gx_freshness.adapters.outbound.great_expectations.rules.base import DataFrameExpectationValidator


class FreshnessValidator(DataFrameExpectationValidator):
    data_source_name = "freshness_runtime"
    data_asset_name = "freshness_results"

    def expectations(self, gx: Any) -> dict[str, Any]:
        return {
            "latest_values_present": gx.expectations.ExpectColumnValuesToNotBeNull(
                column="latest_value"
            ),
            "margin_is_fresh": gx.expectations.ExpectColumnValuesToBeBetween(
                column="freshness_margin_hours",
                min_value=0,
            ),
        }
