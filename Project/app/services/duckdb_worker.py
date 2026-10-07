"""Standalone bounded analytics process. Receives server-controlled JSON on stdin."""

import csv
import io
import json
import sys
from datetime import date, datetime
from decimal import Decimal

import duckdb
import pandas as pd


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


def execute(payload):
    with open(payload["path"], "rb") as source:
        raw = source.read(payload["max_bytes"] + 1)
    if len(raw) > payload["max_bytes"]:
        raise ValueError("File size limit exceeded.")
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    rows = (row for row in reader if row)
    columns = next(rows)
    if columns != payload["columns"]:
        raise ValueError("Stored schema changed.")
    records = []
    for row in rows:
        if len(row) != len(columns) or len(records) >= payload["max_rows"]:
            raise ValueError("Dataset dimensions changed or exceeded limits.")
        records.append(row)
    frame = pd.DataFrame(records, columns=columns, dtype=str)
    types = {c["name"]: c["type"] for c in payload["profile"].get("columns", [])}
    selections = []
    for name in columns:
        quoted = identifier(name)
        if types.get(name) == "number":
            expression = f"CAST(NULLIF(TRIM({quoted}), '') AS DOUBLE)"
        elif types.get(name) == "date":
            expression = f"CAST(NULLIF(TRIM({quoted}), '') AS DATE)"
        else:
            expression = quoted
        selections.append(f"{expression} AS {quoted}")
    with duckdb.connect(
        ":memory:",
        config={
            "memory_limit": f"{payload['memory_mb']}MB",
            "threads": "1",
            "autoinstall_known_extensions": "false",
            "autoload_known_extensions": "false",
            "temp_directory": "",
        },
    ) as connection:
        connection.register("source_frame", frame)
        connection.execute(
            "CREATE TABLE dataset AS SELECT " + ", ".join(selections) + " FROM source_frame"
        )
        connection.unregister("source_frame")
        connection.execute("SET enable_external_access = false")
        connection.execute("SET lock_configuration = true")
        cursor = connection.execute(payload["sql"])
        names = [item[0] for item in cursor.description]
        result = cursor.fetchmany(payload["result_rows"] + 1)
        truncated = len(result) > payload["result_rows"]

        def encode(value):
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if isinstance(value, Decimal):
                return str(value)
            return value

        return {
            "columns": names,
            "rows": [[encode(v) for v in row] for row in result[: payload["result_rows"]]],
            "truncated": truncated,
        }


if __name__ == "__main__":
    try:
        print(json.dumps({"result": execute(json.load(sys.stdin))}, allow_nan=False))
    except Exception:
        # Never expose dataset contents or native exception details to clients.
        print(
            json.dumps({"error": "Query failed. Check column types and supported SQL operations."})
        )
        sys.exit(1)
