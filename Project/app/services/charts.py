"""Build charts from computed rows, never from generated numerical claims."""

import html
import json
import math
from datetime import date

import plotly.graph_objects as go


class ChartError(ValueError):
    pass


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def build_chart(spec, result):
    if spec is None:
        return None
    if result["truncated"]:
        raise ChartError("Chart omitted because the result is truncated. Narrow your question.")
    columns = result["columns"]
    if columns.count(spec.x) != 1 or columns.count(spec.y) != 1:
        raise ChartError("Chart axes must match unique result columns.")
    xi, yi = columns.index(spec.x), columns.index(spec.y)
    pairs = [
        (row[xi], row[yi]) for row in result["rows"] if row[xi] is not None and row[yi] is not None
    ]
    if not pairs:
        raise ChartError("No nonmissing values are available for this chart.")
    x, y = map(list, zip(*pairs))
    if not all(numeric(value) for value in y):
        raise ChartError("The chart value axis must contain finite numbers.")
    if spec.type == "scatter" and not all(numeric(value) for value in x):
        raise ChartError("Scatter charts need numeric values on both axes.")
    if spec.type == "pie" and (any(value < 0 for value in y) or sum(y) <= 0):
        raise ChartError("Pie charts require nonnegative values and a positive total.")
    if spec.type == "line":
        if all(numeric(value) for value in x):
            pairs.sort(key=lambda pair: pair[0])
        else:
            try:
                pairs.sort(key=lambda pair: date.fromisoformat(str(pair[0])[:10]))
            except ValueError as exc:
                raise ChartError(
                    "Line charts need numeric or ISO date values on the horizontal axis."
                ) from exc
        x, y = map(list, zip(*pairs))
    x = [html.escape(value) if isinstance(value, str) else value for value in x]
    if spec.type == "bar":
        trace = go.Bar(x=x, y=y, marker_color="#303136")
    elif spec.type == "pie":
        trace = go.Pie(labels=x, values=y, sort=False)
    else:
        trace = go.Scatter(
            x=x,
            y=y,
            mode="lines+markers" if spec.type == "line" else "markers",
            marker_color="#303136",
        )
    figure = go.Figure(trace)
    figure.update_layout(
        template="plotly_white",
        title_text=html.escape(spec.title),
        font_family="Arial, sans-serif",
        margin=dict(l=60, r=25, t=65, b=60),
        height=420,
        paper_bgcolor="#ffffff",
    )
    if spec.type != "pie":
        figure.update_xaxes(title_text=html.escape(spec.x))
        figure.update_yaxes(title_text=html.escape(spec.y))
    return json.loads(figure.to_json())
