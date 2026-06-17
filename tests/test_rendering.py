from datetime import datetime, timezone
from io import StringIO
import json

import pandas as pd

from gx_freshness.adapters.outbound.output import FreshnessResultRenderer
from gx_freshness.domain import FreshnessRunResult, ValidationSummary


def test_render_json_writes_payload() -> None:
    output = StringIO()
    renderer = FreshnessResultRenderer(output=output)
    result = FreshnessRunResult(
        success=True,
        dataframe=pd.DataFrame(
            [
                {
                    "schema": "main",
                    "table": "orders",
                    "freshness_field": "updated_at",
                    "latest_value": datetime.now(timezone.utc),
                    "age_hours": 0.1,
                    "expected_hours": 2,
                    "freshness_margin_hours": 1.9,
                    "is_fresh": True,
                    "record_count_lookback_hours": None,
                    "expected_record_count": None,
                    "record_count_delta_percent": None,
                    "actual_record_count": None,
                    "record_count_minimum": None,
                    "record_count_maximum": None,
                    "is_record_count_valid": None,
                    "error": None,
                }
            ]
        ),
        validation=ValidationSummary(
            success=True,
            checked_tables=1,
            unexpected_count=0,
            raw_result={},
        ),
    )

    renderer.render(result, json_output=True)

    payload = json.loads(output.getvalue())
    assert payload["success"] is True
    assert payload["tables"][0]["table"] == "orders"
    assert payload["validation"]["checked_tables"] == 1
