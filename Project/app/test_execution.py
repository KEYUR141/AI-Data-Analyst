import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from .services.execution import ExecutionError, execute_analysis
from .services.plan_schemas import AnalysisPlan
from .services.profiling import profile_csv


@pytest.fixture
def dataset(settings, tmp_path):
    settings.PRIVATE_UPLOAD_ROOT = tmp_path
    source = Path(__file__).resolve().parents[2] / "sample_data" / "retail_sales.csv"
    raw = source.read_bytes()
    (tmp_path / "sample.csv").write_bytes(raw)
    profile = profile_csv(SimpleUploadedFile("sample.csv", raw))
    return SimpleNamespace(
        id=uuid4(),
        storage_name="sample.csv",
        profile=profile,
        columns=[c["name"] for c in profile["columns"]],
    )


def plan(dataset, sql):
    return AnalysisPlan(
        action="analyze",
        dataset_id=dataset.id,
        sql=sql,
        explanation="Calculate results.",
        assumptions=[],
        chart=None,
    )


def test_known_revenue_and_highest_product(dataset):
    result = execute_analysis(
        plan(
            dataset,
            "SELECT region, SUM(revenue) AS total FROM dataset GROUP BY region ORDER BY total DESC",
        ),
        dataset,
    )
    assert result["rows"] == [
        ["South", 27000.0],
        ["North", 25350.0],
        ["West", 7120.0],
        ["East", 2250.0],
    ]
    assert not result["truncated"]
    result = execute_analysis(
        plan(
            dataset,
            "SELECT product, SUM(revenue) AS total FROM dataset GROUP BY product ORDER BY total DESC LIMIT 1",
        ),
        dataset,
    )
    assert result["rows"] == [["Desk", 27000.0]]


def test_monthly_dates_and_nulls(dataset):
    result = execute_analysis(
        plan(
            dataset,
            "SELECT DATE_TRUNC('month', date) AS month, SUM(revenue) AS total FROM dataset GROUP BY month ORDER BY month",
        ),
        dataset,
    )
    assert len(result["rows"]) == 6
    assert result["rows"][0][0].startswith("2026-01-01")
    assert sum(row[1] for row in result["rows"]) == 61720
    result = execute_analysis(
        plan(dataset, "SELECT COUNT(*) AS rows, COUNT(revenue) AS revenue_rows FROM dataset"),
        dataset,
    )
    assert result["rows"] == [[121, 120]]


def test_result_limit(dataset, settings):
    settings.ANALYSIS_MAX_RESULT_ROWS = 2
    result = execute_analysis(plan(dataset, "SELECT order_id FROM dataset"), dataset)
    assert len(result["rows"]) == 2
    assert result["truncated"]


def test_invalid_query_rejected_before_process(dataset):
    with patch("app.services.execution.subprocess.run") as run:
        with pytest.raises(ExecutionError):
            execute_analysis(plan(dataset, "SELECT * FROM read_csv('/secret')"), dataset)
        run.assert_not_called()


def test_timeout_is_reported(dataset):
    with patch(
        "app.services.execution.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 1)
    ):
        with pytest.raises(ExecutionError, match="timed out"):
            execute_analysis(plan(dataset, "SELECT * FROM dataset"), dataset)


def test_sample_anomaly_runs_in_real_worker(dataset):
    from .services.plan_schemas import AnomalyPlan

    anomaly = AnomalyPlan(
        action="anomalies",
        dataset_id=dataset.id,
        columns=["revenue"],
        explanation="Apply IQR fences.",
        assumptions=[],
    )
    output = execute_analysis(anomaly, dataset)
    assert output["flag_count"] >= 1
    assert any(row[0] == 11 and row[2] == 12000 for row in output["rows"])
