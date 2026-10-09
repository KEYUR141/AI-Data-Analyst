from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError

from .models import Dataset
from .services.datasets import private_storage, save_dataset
from .testing import authenticated_client


@pytest.fixture(autouse=True)
def isolated_storage(settings, tmp_path):
    settings.PRIVATE_UPLOAD_ROOT = tmp_path / "uploads"


def file(content=b"product,revenue\nWidget,12\n", name="sales.csv"):
    return SimpleUploadedFile(name, content)


@pytest.mark.django_db
def test_upload_preview_and_delete():
    client = authenticated_client()
    response = client.post("/datasets/upload/", {"files": file()})
    assert response.status_code == 302
    dataset = Dataset.objects.get()
    assert dataset.profile["row_count"] == 1
    assert dataset.profile["columns"][1]["type"] == "number"
    assert dataset.owner_session == client.session.session_key
    assert dataset.storage_name != dataset.original_name
    with private_storage().open(dataset.storage_name, "rb") as stored:
        assert stored.read() == b"product,revenue\nWidget,12\n"
    assert b"Widget" in client.get(f"/datasets/{dataset.id}/").content
    assert b"sales.csv" in client.get("/").content
    assert client.post(f"/datasets/{dataset.id}/delete/").status_code == 302
    assert not Dataset.objects.exists()
    assert not private_storage().exists(dataset.storage_name)


@pytest.mark.django_db
def test_other_session_cannot_access_or_delete():
    owner, stranger = authenticated_client(), authenticated_client()
    owner.post("/datasets/upload/", {"files": file()})
    dataset = Dataset.objects.get()
    assert stranger.get(f"/datasets/{dataset.id}/").status_code == 404
    assert stranger.post(f"/datasets/{dataset.id}/delete/").status_code == 404
    assert b"sales.csv" not in stranger.get("/").content
    assert Dataset.objects.count() == 1


@pytest.mark.django_db
def test_mixed_batch_persists_only_valid_file():
    authenticated_client().post("/datasets/upload/", {"files": [file(), file(b"", "empty.csv")]})
    assert list(Dataset.objects.values_list("original_name", flat=True)) == ["sales.csv"]
    assert len(list(private_storage().listdir("")[1])) == 1


@pytest.mark.django_db
def test_database_failure_removes_saved_file():
    with patch("app.services.datasets.Dataset.objects.create", side_effect=DatabaseError):
        with pytest.raises(DatabaseError):
            save_dataset(file(), "owner")
    assert private_storage().listdir("")[1] == []


@pytest.mark.django_db
def test_preview_escapes_uploaded_html():
    client = authenticated_client()
    client.post("/datasets/upload/", {"files": file(b"column\n<script>alert(1)</script>\n")})
    response = client.get(f"/datasets/{Dataset.objects.get().id}/")
    assert b"&lt;script&gt;" in response.content
    assert b"<script>alert(1)</script>" not in response.content


def test_upload_requires_csrf_and_post():
    assert authenticated_client().get("/datasets/upload/").status_code == 405
    assert (
        authenticated_client(enforce_csrf_checks=True)
        .post("/datasets/upload/", {"files": file()})
        .status_code
        == 403
    )


pytestmark = pytest.mark.django_db
