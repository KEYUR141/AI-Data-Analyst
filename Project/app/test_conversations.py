from unittest.mock import patch

import pytest

from .models import AnalysisRun, Conversation, Dataset
from .services.plan_schemas import ClarificationPlan
from .services.planning import PlanningError
from .testing import authenticated_client


@pytest.mark.django_db
def test_history_survives_refresh_and_clarification_replies():
    client = authenticated_client()
    session = client.session
    session.save()
    dataset = Dataset.objects.create(
        owner_session=session.session_key,
        owner=client.test_user,
        original_name="a.csv",
        storage_name="test.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    url = f"/datasets/{dataset.id}/plan/"
    with patch("app.planning_views.generate_plan") as generate:
        generate.return_value = ClarificationPlan(action="clarify", question="Which metric?")
        assert client.post(url, {"question": "Show performance"}).status_code == 200
        assert generate.call_args.kwargs["history"] == []
        assert client.post(url, {"question": "Revenue"}).status_code == 200
        assert generate.call_args.kwargs["history"][0]["question"] == "Show performance"
        assert Conversation.objects.count() == 1
        assert AnalysisRun.objects.count() == 2
        page = client.get(f"/datasets/{dataset.id}/")
        assert b"Show performance" in page.content
        assert b"Which metric?" in page.content
        generate.side_effect = PlanningError("Unavailable")
        assert client.post(url, {"question": "Failed request"}).status_code == 502
        generate.side_effect = None
        assert client.post(url, {"question": "Retry"}).status_code == 200
        assert all(
            entry["question"] != "Failed request" for entry in generate.call_args.kwargs["history"]
        )
        assert authenticated_client().get(f"/datasets/{dataset.id}/").status_code == 404


pytestmark = pytest.mark.django_db
