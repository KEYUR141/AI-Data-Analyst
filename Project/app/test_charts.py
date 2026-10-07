import pytest

from .services.charts import ChartError, build_chart
from .services.plan_schemas import Chart


@pytest.mark.parametrize("kind", ["bar", "line", "pie", "scatter"])
def test_required_chart_types(kind):
    spec = Chart(type=kind, x="x", y="y", title="Test")
    result = {"columns": ["x", "y"], "rows": [[2, 10], [1, 20]], "truncated": False}
    chart = build_chart(spec, result)
    assert chart["data"][0]["type"] == ("scatter" if kind in ["line", "scatter"] else kind)
    if kind == "line":
        assert chart["data"][0]["x"] == [1, 2]


@pytest.mark.parametrize(
    "columns,rows,truncated,kind",
    [
        (["wrong", "y"], [[1, 2]], False, "bar"),
        (["x", "y"], [[1, "text"]], False, "bar"),
        (["x", "y"], [[1, -2]], False, "pie"),
        (["x", "y"], [[1, 0]], False, "pie"),
        (["x", "y"], [["category", 2]], False, "scatter"),
        (["x", "y"], [["category", 2]], False, "line"),
        (["x", "y"], [[None, 2]], False, "bar"),
        (["x", "y"], [[1, 2]], True, "pie"),
    ],
)
def test_invalid_chart_preserves_results(columns, rows, truncated, kind):
    with pytest.raises(ChartError):
        build_chart(
            Chart(type=kind, x="x", y="y", title="Test"),
            {"columns": columns, "rows": rows, "truncated": truncated},
        )


def test_date_sorting_and_escaping():
    chart = build_chart(
        Chart(type="line", x="date", y="total", title="<b>Sales</b>"),
        {
            "columns": ["date", "total"],
            "rows": [["2026-02-01", 10], ["2026-01-01", 20]],
            "truncated": False,
        },
    )
    assert chart["data"][0]["x"][0] == "2026-01-01"
    assert chart["layout"]["title"]["text"] == "&lt;b&gt;Sales&lt;/b&gt;"
