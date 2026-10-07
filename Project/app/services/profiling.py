"""Describe validated CSV values without modifying their stored representation."""

import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext

import pandas as pd

NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
LEADING_ZERO = re.compile(r"[+-]?0\d")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def column_profile(name, series):
    # Whitespace-only cells count as missing, but source strings remain untouched.
    values = [value.strip() for value in series.tolist() if value.strip()]
    result = {
        "name": name,
        "type": "empty" if not values else "text",
        "missing_count": len(series) - len(values),
        "distinct_count": len(set(values)),
        "statistics": {},
    }
    if not values:
        return result
    if all(ISO_DATE.fullmatch(value) for value in values):
        try:
            dates = [date.fromisoformat(value) for value in values]
        except ValueError:
            pass
        else:
            result["type"] = "date"
            result["statistics"] = {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat(),
            }
            return result
    if all(NUMBER.fullmatch(value) and not LEADING_ZERO.match(value) for value in values):
        try:
            numbers = [Decimal(value) for value in values]
            # Avoid pathological exponents/precision and nonfinite JSON values.
            if any(
                not n.is_finite() or abs(n.adjusted()) > 100 or len(n.as_tuple().digits) > 100
                for n in numbers
            ):
                return result
            with localcontext() as context:
                context.prec = 220
                ordered = sorted(numbers)
                midpoint = len(ordered) // 2
                median = (
                    ordered[midpoint]
                    if len(ordered) % 2
                    else (ordered[midpoint - 1] + ordered[midpoint]) / 2
                )
                stats = {
                    "minimum": min(numbers),
                    "maximum": max(numbers),
                    "mean": sum(numbers) / len(numbers),
                    "median": median,
                }
                result["statistics"] = {key: str(value) for key, value in stats.items()}
            result["type"] = "number"
        except InvalidOperation:
            pass
    return result


def profile_csv(upload):
    """Profile all rows of a previously validated, size-bounded upload.

    Reuse Python's CSV record semantics, including blank-line behavior. Pandas
    holds original string values and counts exact duplicate rows. Statistics
    use decimal arithmetic; JSON stores numbers as strings to avoid precision loss.
    """
    try:
        upload.seek(0)
        reader = csv.reader(io.StringIO(upload.read().decode("utf-8-sig"), newline=""), strict=True)
        rows = (row for row in reader if row)
        columns = next(rows)
        frame = pd.DataFrame(list(rows), columns=columns, dtype=str)
        return {
            "version": 1,
            "row_count": len(frame),
            "duplicate_row_count": int(frame.duplicated().sum()),
            "columns": [column_profile(name, frame[name]) for name in columns],
        }
    finally:
        upload.seek(0)
