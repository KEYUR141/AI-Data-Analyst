"""Persistence follows successful validation; storage uses generated names."""

import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction

from app.models import Dataset

from .profiling import profile_csv
from .validation import CSVLimits, validate_csv


def private_storage():
    return FileSystemStorage(location=settings.PRIVATE_UPLOAD_ROOT)


def save_dataset(upload, owner_session):
    limits = CSVLimits(
        settings.CSV_MAX_BYTES,
        settings.CSV_MAX_ROWS,
        settings.CSV_MAX_COLUMNS,
        settings.CSV_PREVIEW_ROWS,
    )
    validated = validate_csv(upload, limits)
    profile = profile_csv(upload)
    storage = private_storage()
    name = storage.save(f"{uuid.uuid4().hex}.csv", upload)
    try:
        with transaction.atomic():
            return Dataset.objects.create(
                owner_session=owner_session,
                original_name=upload.name,
                storage_name=name,
                size_bytes=validated.size_bytes,
                row_count=validated.row_count,
                columns=validated.columns,
                preview=validated.preview,
                profile=profile,
            )
    except Exception:
        # A database failure must not leave a successfully saved orphan file.
        storage.delete(name)
        raise


def delete_dataset(dataset):
    # Delete the file first; a storage failure leaves metadata available for retry.
    private_storage().delete(dataset.storage_name)
    dataset.delete()
