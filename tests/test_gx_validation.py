from datetime import datetime, timezone

import pandas as pd

from gx_freshness.adapters.outbound.great_expectations import validate_freshness_frame


def test_validate_freshness_frame_succeeds_for_fresh_rows() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "schema": "public",
                "table": "orders",
                "freshness_field": "updated_at",
                "latest_value": datetime.now(timezone.utc),
                "age_hours": 0.5,
                "expected_hours": 2,
                "freshness_margin_hours": 1.5,
                "is_fresh": True,
                "error": None,
            }
        ]
    )

    result = validate_freshness_frame(dataframe)

    assert result.success is True
    assert result.checked_tables == 1
    assert result.unexpected_count == 0


def test_validate_freshness_frame_succeeds_for_record_count_inside_tolerance() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "schema": "public",
                "table": "orders",
                "freshness_field": "updated_at",
                "latest_value": datetime.now(timezone.utc),
                "age_hours": 0.5,
                "expected_hours": 2,
                "freshness_margin_hours": 1.5,
                "is_fresh": True,
                "record_count_lookback_hours": 1,
                "expected_record_count": 100,
                "record_count_delta_percent": 10,
                "record_count_minimum": 90,
                "record_count_maximum": 110,
                "actual_record_count": 94,
                "is_record_count_valid": True,
                "error": None,
            }
        ]
    )

    result = validate_freshness_frame(dataframe)

    assert result.success is True
    assert result.unexpected_count == 0
    assert len(result.raw_result["record_count_in_tolerance"]) == 2
