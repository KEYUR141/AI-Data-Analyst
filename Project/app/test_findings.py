from types import SimpleNamespace
from uuid import uuid4

import pandas as pd

from .services.duckdb_worker import anomaly_results
from .services.planning import validate_plan
from .services.summaries import summarize


def test_iqr_flags_explained_and_bounded():
    frame = pd.DataFrame({"revenue": ["10", "11", "12", "13", "14", "15", "16", "100", "200", ""]})
    result = anomaly_results(frame, {"anomaly_columns": ["revenue"], "result_rows": 1})
    assert result["flag_count"] == 2
    assert result["truncated"]
    assert result["rows"][0][0] == 8
    assert result["rows"][0][-1] == "Above upper fence"
    assert "IQR" in summarize(result)


def test_small_samples_and_constant_values():
    frame = pd.DataFrame({"small": ["1", "", "", ""], "constant": ["2", "2", "2", "2"]})
    result = anomaly_results(frame, {"anomaly_columns": ["small", "constant"], "result_rows": 10})
    assert result["flag_count"] == 0
    assert "fewer than four" in result["method_notes"][0]
    assert "zero IQR" in result["method_notes"][1]


def test_summary_uses_computed_result_and_handles_empty():
    output = {
        "columns": ["region", "revenue"],
        "rows": [["South", 27000], ["East", 2250]],
        "truncated": False,
    }
    summary = summarize(output)
    assert "South" in summary and "27000" in summary
    assert summarize({**output, "rows": []}) == "No records matched the analysis."


def test_anomaly_plan_validates_numeric_schema():
    import json

    dataset = SimpleNamespace(
        id=uuid4(), profile={"columns": [{"name": "revenue", "type": "number"}]}
    )
    text = json.dumps(
        {
            "action": "anomalies",
            "dataset_id": str(dataset.id),
            "columns": ["revenue"],
            "explanation": "Detect outliers.",
            "assumptions": [],
        }
    )
    assert validate_plan(text, dataset).action == "anomalies"
