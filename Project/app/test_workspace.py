import pytest

from .models import Conversation, Dataset
from .testing import authenticated_client


@pytest.mark.django_db
def test_new_threads_are_independent_and_private():
    client = authenticated_client()
    session = client.session
    session.save()
    dataset = Dataset.objects.create(
        owner_session=session.session_key,
        owner=client.test_user,
        original_name="a.csv",
        storage_name="workspace.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    first = client.post(
        "/threads/new/", {"dataset_id": dataset.id, "question": "First question"}
    ).json()
    second = client.post(
        "/threads/new/", {"dataset_id": dataset.id, "question": "Second question"}
    ).json()
    assert first["id"] != second["id"]
    assert Conversation.objects.count() == 2
    page = client.get(f"/threads/{first['id']}/")
    assert page.status_code == 200
    assert b"First question" in page.content
    assert b"Second question" in page.content
    assert authenticated_client().get(f"/threads/{first['id']}/").status_code == 404
    assert (
        authenticated_client().post("/threads/new/", {"dataset_id": dataset.id}).status_code == 404
    )
    assert client.post("/threads/new/", {"dataset_id": "bad"}).status_code == 400
    landing = client.get("/")
    assert landing.context["conversation"] is None


pytestmark = pytest.mark.django_db
