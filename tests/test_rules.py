import pandas as pd

from gx_freshness.adapters.outbound.great_expectations.rules.record_count import RecordCountValidator


def test_record_count_validator_filters_to_configured_rows() -> None:
    dataframe = pd.DataFrame(
        [
            {"table": "orders", "expected_record_count": 10},
            {"table": "audit_log", "expected_record_count": None},
        ]
    )

    filtered = RecordCountValidator().filter_dataframe(dataframe)

    assert filtered["table"].tolist() == ["orders"]


def test_record_count_validator_empty_result_matches_public_raw_shape() -> None:
    result = RecordCountValidator().empty_raw_result()

    assert result == {"record_count_in_tolerance": []}
