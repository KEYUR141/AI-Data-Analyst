import pytest
from django.core.exceptions import ValidationError

from .models import AnalysisRun, Conversation, Dataset, Message


@pytest.mark.django_db
def test_persistence_and_dataset_cascade():
    dataset = Dataset.objects.create(
        owner_session="owner",
        original_name="a.csv",
        storage_name="model-test.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    conversation = Conversation.objects.create(owner_session="owner", dataset=dataset)
    user = Message.objects.create(
        conversation=conversation, role=Message.Role.USER, content="Total?"
    )
    assistant = Message.objects.create(
        conversation=conversation, role=Message.Role.ASSISTANT, content="One."
    )
    run = AnalysisRun.objects.create(
        user_message=user,
        assistant_message=assistant,
        status=AnalysisRun.Status.COMPLETED,
        result={"rows": [[1]]},
    )
    run.full_clean()
    run.refresh_from_db()
    assert run.result == {"rows": [[1]]}
    dataset.delete()
    assert not Conversation.objects.exists()
    assert not Message.objects.exists()
    assert not AnalysisRun.objects.exists()


@pytest.mark.django_db
def test_response_cannot_come_from_another_conversation():
    dataset = Dataset.objects.create(
        owner_session="owner",
        original_name="a.csv",
        storage_name="model-test.csv",
        size_bytes=4,
        row_count=1,
        columns=["a"],
        preview=[["1"]],
    )
    first = Conversation.objects.create(owner_session="owner", dataset=dataset)
    second = Conversation.objects.create(owner_session="owner", dataset=dataset)
    user = Message.objects.create(conversation=first, role="user", content="Question")
    assistant = Message.objects.create(conversation=second, role="assistant", content="Answer")
    with pytest.raises(ValidationError):
        AnalysisRun(user_message=user, assistant_message=assistant).full_clean()
