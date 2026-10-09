"""Grounded, deterministic findings from computed output; no invented metrics."""


def summarize(output):
    if "flag_count" in output:
        return (
            f"Detected {output['flag_count']} statistical outlier flags using 1.5 × IQR fences. "
            + " ".join(output.get("method_notes", []))
        )
    rows, columns = output["rows"], output["columns"]
    if not rows:
        return "No records matched the analysis."

    def describe(row):
        return "; ".join(
            f"{name}: {value if value is not None else 'missing'}"
            for name, value in zip(columns, row)
        )

    if len(rows) == 1:
        return "Result — " + describe(rows[0]) + "."
    summary = f"Returned {'at least ' if output['truncated'] else ''}{len(rows)} result rows. "
    summary += "First result in query order — " + describe(rows[0]) + ". "
    for index, name in enumerate(columns):
        values = [
            (row[index], row)
            for row in rows
            if isinstance(row[index], (int, float)) and not isinstance(row[index], bool)
        ]
        if values:
            maximum, row = max(values, key=lambda pair: pair[0])
            summary += f"Highest {name} in the returned rows is {maximum}: " + describe(row) + ". "
            break
    if output["truncated"]:
        summary += "Results are truncated; these findings describe only the returned rows."
    return summary.strip()
