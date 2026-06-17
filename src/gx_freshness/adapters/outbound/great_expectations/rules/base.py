from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ValidatorResult:
    success: bool
    unexpected_count: int
    raw_result: dict[str, Any]


class DataFrameExpectationValidator(ABC):
    data_source_name: str
    data_asset_name: str

    def validate(self, gx: Any, context: Any, dataframe: pd.DataFrame) -> ValidatorResult:
        validation_frame = self.filter_dataframe(dataframe)
        if validation_frame.empty:
            return ValidatorResult(success=True, unexpected_count=0, raw_result=self.empty_raw_result())

        batch = self._build_batch(context, validation_frame)
        results = {
            expectation_name: batch.validate(expectation)
            for expectation_name, expectation in self.expectations(gx).items()
        }

        return ValidatorResult(
            success=all(result.success for result in results.values()),
            unexpected_count=sum(_unexpected_count(result) for result in results.values()),
            raw_result=self.raw_result(results),
        )

    def filter_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return dataframe

    @abstractmethod
    def expectations(self, gx: Any) -> dict[str, Any]:
        raise NotImplementedError

    def empty_raw_result(self) -> dict[str, Any]:
        return {}

    def raw_result(self, results: dict[str, Any]) -> dict[str, Any]:
        return {name: result.to_json_dict() for name, result in results.items()}

    def _build_batch(self, context: Any, dataframe: pd.DataFrame) -> Any:
        data_source = context.data_sources.add_pandas(name=self.data_source_name)
        data_asset = data_source.add_dataframe_asset(name=self.data_asset_name)
        batch_definition = data_asset.add_batch_definition_whole_dataframe("whole_dataframe")
        return batch_definition.get_batch(batch_parameters={"dataframe": dataframe})


def _unexpected_count(result: Any) -> int:
    result_dict = result.to_json_dict()
    value = result_dict.get("result", {}).get("unexpected_count")
    return int(value or 0)
