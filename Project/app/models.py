import uuid

from django.conf import settings
from django.db import models


class Dataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session = models.CharField(max_length=40, db_index=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    original_name = models.CharField(max_length=255)
    storage_name = models.CharField(max_length=255, unique=True)
    size_bytes = models.PositiveBigIntegerField()
    row_count = models.PositiveIntegerField()
    columns = models.JSONField()
    preview = models.JSONField()
    profile = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session = models.CharField(max_length=40, db_index=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    # Removing a dataset also removes its related conversation history.
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, default="New conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "id"]

    def __str__(self):
        return self.title


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["user", "assistant"]), name="message_valid_role"
            ),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"


class AnalysisRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        CLARIFICATION = "clarification", "Clarification needed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # The conversation and dataset are reached through the initiating message.
    # Avoid duplicating foreign keys that could disagree with each other.
    user_message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="analysis_run"
    )
    assistant_message = models.OneToOneField(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="response_run",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    plan = models.JSONField(default=dict, blank=True)
    executed_sql = models.TextField(blank=True)
    # Store bounded execution results, not the full uploaded dataset.
    result = models.JSONField(default=dict, blank=True)
    chart_spec = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    status__in=["pending", "running", "completed", "clarification", "failed"]
                ),
                name="analysis_valid_status",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.user_message_id and self.user_message.role != Message.Role.USER:
            raise ValidationError({"user_message": "An analysis must start from a user message."})
        if self.assistant_message_id:
            if self.assistant_message.role != Message.Role.ASSISTANT:
                raise ValidationError(
                    {"assistant_message": "The response must be an assistant message."}
                )
            if (
                self.user_message_id
                and self.assistant_message.conversation_id != self.user_message.conversation_id
            ):
                raise ValidationError(
                    {"assistant_message": "Both messages must belong to the same conversation."}
                )
