import json
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from .services.planning import PlanningError, generate_plan, validate_plan
from .services.sql_validator import InvalidSQL, validate_sql
from .testing import authenticated_client


@pytest.fixture
def dataset():
    return SimpleNamespace(id=uuid4(), columns=["region", "revenue"], profile={})


def analysis(dataset, **changes):
    plan = dict(
        action="analyze",
        dataset_id=str(dataset.id),
        sql="SELECT region, SUM(revenue) AS total FROM dataset GROUP BY region ORDER BY total DESC",
        explanation="Sum revenue by region.",
        assumptions=[],
        chart=None,
    )
    return json.dumps(plan | changes)


def test_valid_analysis_and_clarification(dataset):
    assert validate_plan(analysis(dataset), dataset).action == "analyze"
    assert (
        validate_plan('{"action":"clarify","question":"Which metric?"}', dataset).action
        == "clarify"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"dataset_id": str(uuid4())},
        {"action": "execute"},
        {"sql": "DELETE FROM dataset"},
        {"extra": "not allowed"},
        {"explanation": " "},
        {"chart": {"type": "unknown", "x": "region", "y": "total", "title": "Revenue"}},
    ],
)
def test_rejects_invalid_plan(dataset, changes):
    with pytest.raises(PlanningError):
        validate_plan(analysis(dataset, **changes), dataset)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM other",
        "SELECT * FROM main.dataset",
        "SELECT * FROM read_csv('/secret.csv')",
        "SELECT read_blob('/secret') FROM dataset",
        "SELECT * FROM dataset; DROP TABLE dataset",
        "SELECT missing FROM dataset",
        "SELECT * FROM dataset JOIN dataset AS b ON true",
        "WITH x AS (SELECT * FROM dataset) SELECT * FROM x",
        "SELECT (SELECT revenue FROM dataset) FROM dataset",
        "COPY dataset TO 'x.csv'",
        "SELECT * INTO other FROM dataset",
    ],
)
def test_restricted_sql(sql):
    with pytest.raises(InvalidSQL):
        validate_sql(sql, ["region", "revenue"])


def test_group_and_having_can_reference_output_aliases():
    sql = "SELECT region AS area, SUM(revenue) AS total FROM dataset GROUP BY area HAVING total > 0 ORDER BY total"
    assert validate_sql(sql, ["region", "revenue"])


def test_highest_grossing_product_needs_no_subquery():
    sql = "SELECT product, SUM(revenue) AS total_revenue FROM dataset GROUP BY product ORDER BY total_revenue DESC LIMIT 1"
    assert validate_sql(sql, ["product", "revenue"])


def test_unsupported_sql_gets_one_validated_repair(dataset, settings):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_MODEL = "test-model"
    with patch("app.services.planning.create_gemini_client") as factory:
        generate = factory.return_value.__enter__.return_value.models.generate_content
        invalid = analysis(dataset, sql="SELECT * FROM (SELECT * FROM dataset) x")
        generate.side_effect = [
            SimpleNamespace(text=invalid),
            SimpleNamespace(text=analysis(dataset)),
        ]
        assert generate_plan("Highest revenue?", dataset).action == "analyze"
        assert generate.call_count == 2


def test_repair_is_bounded_and_still_rejects_unsafe_sql(dataset, settings):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_MODEL = "test-model"
    with patch("app.services.planning.create_gemini_client") as factory:
        generate = factory.return_value.__enter__.return_value.models.generate_content
        generate.return_value.text = analysis(dataset, sql="DELETE FROM dataset")
        with pytest.raises(PlanningError):
            generate_plan("Highest revenue?", dataset)
        assert generate.call_count == 2


def test_alias_is_not_allowed_in_where():
    with pytest.raises(InvalidSQL):
        validate_sql("SELECT region AS area FROM dataset WHERE area = 1", ["region"])


def test_sql_error_explains_restriction(dataset):
    with pytest.raises(PlanningError, match="unknown column"):
        validate_plan(analysis(dataset, sql="SELECT nonexistent FROM dataset"), dataset)


def test_generation_is_structured_and_sends_no_preview(dataset, settings):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_MODEL = "test-model"
    dataset.preview = [["PRIVATE_VALUE"]]
    with patch("app.services.planning.create_gemini_client") as factory:
        client = factory.return_value.__enter__.return_value
        client.models.generate_content.return_value.text = analysis(dataset)
        assert generate_plan("Revenue by region", dataset).action == "analyze"
        args = client.models.generate_content.call_args.kwargs
        assert "PRIVATE_VALUE" not in args["contents"]
        assert args["config"].response_mime_type == "application/json"
        assert args["config"].response_json_schema
        factory.return_value.__exit__.assert_called_once()


def test_provider_timeout_is_sanitized(dataset, settings):
    settings.GEMINI_API_KEY = "test-key"
    settings.GEMINI_MODEL = "test-model"
    with patch("app.services.planning.create_gemini_client") as factory:
        factory.return_value.__enter__.return_value.models.generate_content.side_effect = (
            httpx.ReadTimeout("secret")
        )
        with pytest.raises(PlanningError, match="timed out"):
            generate_plan("Revenue", dataset)


@pytest.mark.django_db
def test_endpoint_ownership_and_plan_response():
    from .models import Dataset
    from .services.plan_schemas import ClarificationPlan

    # Create metadata directly: this test never writes a private file.
    owner = authenticated_client()
    session = owner.session
    session.save()
    dataset = Dataset.objects.create(
        owner_session=session.session_key,
        owner=owner.test_user,
        original_name="data.csv",
        storage_name="test.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    with patch("app.planning_views.generate_plan") as generate:
        assert (
            authenticated_client()
            .post(f"/datasets/{dataset.id}/plan/", {"question": "Revenue"})
            .status_code
            == 404
        )
        generate.assert_not_called()
        assert owner.post(f"/datasets/{dataset.id}/plan/", {"question": ""}).status_code == 400
        generate.return_value = ClarificationPlan(action="clarify", question="Which metric?")
        response = owner.post(f"/datasets/{dataset.id}/plan/", {"question": "Revenue"})
        assert response.status_code == 200
        assert response.json()["executed"] is False


pytestmark = pytest.mark.django_db
