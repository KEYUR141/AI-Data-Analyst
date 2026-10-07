import json
import subprocess
import sys
import time
from pathlib import Path

from django.conf import settings

from .datasets import private_storage
from .sql_validator import InvalidSQL, validate_sql


class ExecutionError(ValueError):
    pass


def execute_analysis(plan, dataset):
    if plan.dataset_id != dataset.id:
        raise ExecutionError("Analysis does not match the selected dataset.")
    try:
        sql = validate_sql(plan.sql, dataset.columns)
    except InvalidSQL as exc:
        raise ExecutionError(str(exc)) from exc
    payload = {
        "path": private_storage().path(dataset.storage_name),
        "sql": sql,
        "columns": dataset.columns,
        "profile": dataset.profile,
        "max_bytes": settings.CSV_MAX_BYTES,
        "max_rows": settings.CSV_MAX_ROWS,
        "memory_mb": settings.ANALYSIS_MEMORY_MB,
        "result_rows": settings.ANALYSIS_MAX_RESULT_ROWS,
    }
    if min(settings.ANALYSIS_TIMEOUT_SECONDS, payload["memory_mb"], payload["result_rows"]) < 1:
        raise ExecutionError("Analysis limits must be positive.")
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("duckdb_worker.py"))],
            input=json.dumps(payload),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=settings.ANALYSIS_TIMEOUT_SECONDS,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExecutionError("Analysis timed out. Try a simpler question.") from exc
    except OSError as exc:
        raise ExecutionError("Analysis worker could not start.") from exc
    try:
        response = json.loads(completed.stdout)
    except (ValueError, TypeError) as exc:
        raise ExecutionError("Analysis worker failed to return results.") from exc
    if completed.returncode or "error" in response:
        raise ExecutionError(response.get("error", "Analysis worker failed."))
    return {
        **response["result"],
        "sql": sql,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "notes": [
            "Blank numeric/date values are treated as NULL.",
            "Duplicate rows are retained. Numeric columns use floating-point arithmetic.",
        ],
    }
