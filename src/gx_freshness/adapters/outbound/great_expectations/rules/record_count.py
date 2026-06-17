from __future__ import annotations

from typing import Any

import pandas as pd

from gx_freshness.adapters.outbound.great_expectations.rules.base import DataFrameExpectationValidator


class RecordCountValidator(DataFrameExpectationValidator):
    data_source_name = "record_count_runtime"
    data_asset_name = "record_count_results"

    def filter_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        if "expected_record_count" not in dataframe.columns:
            return dataframe.iloc[0:0].copy()
        return dataframe[dataframe["expected_record_count"].notna()].copy()

    def expectations(self, gx: Any) -> dict[str, Any]:
        return {
            "record_count_minimum": gx.expectations.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="actual_record_count",
                column_B="record_count_minimum",
                or_equal=True,
            ),
            "record_count_maximum": gx.expectations.ExpectColumnPairValuesAToBeGreaterThanB(
                column_A="record_count_maximum",
                column_B="actual_record_count",
                or_equal=True,
            ),
        }

    def empty_raw_result(self) -> dict[str, Any]:
        return {"record_count_in_tolerance": []}

    def raw_result(self, results: dict[str, Any]) -> dict[str, Any]:
        return {
            "record_count_in_tolerance": [
                results["record_count_minimum"].to_json_dict(),
                results["record_count_maximum"].to_json_dict(),
            ]
        }
