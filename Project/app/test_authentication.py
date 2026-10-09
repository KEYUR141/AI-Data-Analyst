import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from .models import Conversation, Dataset

pytestmark = pytest.mark.django_db


def test_signup_login_logout_and_legacy_claim():
    client = Client()
    session = client.session
    session.save()
    dataset = Dataset.objects.create(
        owner_session=session.session_key,
        original_name="a.csv",
        storage_name="legacy.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    thread = Conversation.objects.create(owner_session=session.session_key, dataset=dataset)
    response = client.post(
        "/accounts/signup/",
        {
            "username": "analyst",
            "password1": "Strong-example-882!",
            "password2": "Strong-example-882!",
        },
    )
    assert response.status_code == 302
    dataset.refresh_from_db()
    thread.refresh_from_db()
    assert dataset.owner == get_user_model().objects.get(username="analyst")
    assert thread.owner == dataset.owner
    assert client.get("/").status_code == 200
    assert client.get("/accounts/logout/").status_code == 405
    assert client.post("/accounts/logout/").status_code == 302
    assert client.get("/").status_code == 302
    assert (
        client.post(
            "/accounts/login/", {"username": "analyst", "password": "Strong-example-882!"}
        ).status_code
        == 302
    )
    assert client.get(f"/threads/{thread.id}/").status_code == 200


def test_login_rejects_bad_password_and_templates_render():
    client = Client()
    assert client.get("/accounts/login/").status_code == 200
    assert client.get("/accounts/signup/").status_code == 200
    response = client.post("/accounts/login/", {"username": "missing", "password": "wrong"})
    assert response.status_code == 200
    assert client.get("/").status_code == 302
