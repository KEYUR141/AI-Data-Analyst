import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Dataset
from .services.datasets import delete_dataset, save_dataset

logger = logging.getLogger(__name__)


@login_required
@require_POST
def upload(request):
    files = request.FILES.getlist("files")
    if not files or len(files) > settings.CSV_MAX_FILES:
        messages.error(request, f"Choose between 1 and {settings.CSV_MAX_FILES} CSV files.")
        return redirect("app:home")
    if not request.session.session_key:
        request.session.create()
    for file in files:
        try:
            save_dataset(file, request.session.session_key, owner=request.user)
        except ValidationError as exc:
            messages.error(request, f"{file.name}: {exc.messages[0]}")
        except (OSError, DatabaseError):
            logger.error("Dataset persistence failed")
            messages.error(request, f"{file.name}: Could not save this file. Please try again.")
        else:
            messages.success(request, f"{file.name}: Uploaded successfully.")
    return redirect("app:home")


def owned_dataset(request, dataset_id):
    return get_object_or_404(Dataset, id=dataset_id, owner=request.user)


@login_required
@require_GET
def preview(request, dataset_id):
    from .models import AnalysisRun

    dataset = owned_dataset(request, dataset_id)
    history = list(
        AnalysisRun.objects.filter(
            user_message__conversation__dataset=dataset,
            user_message__conversation__owner=request.user,
        )
        .select_related("user_message", "assistant_message")
        .order_by("-created_at", "-id")[:20]
    )
    return render(
        request, "app/preview.html", {"dataset": dataset, "chat_history": reversed(history)}
    )


@login_required
@require_POST
def remove(request, dataset_id):
    dataset = owned_dataset(request, dataset_id)
    try:
        delete_dataset(dataset)
    except (OSError, DatabaseError):
        logger.error("Dataset removal failed")
        messages.error(request, "Could not remove the dataset. Please try again.")
    else:
        messages.success(request, "Dataset removed.")
    return redirect("app:home")
