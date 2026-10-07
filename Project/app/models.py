import uuid

from django.db import models


class Dataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_session = models.CharField(max_length=40, db_index=True)
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
