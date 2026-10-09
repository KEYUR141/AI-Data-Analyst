from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, Dataset


@login_required
@require_GET
def workspace(request, conversation_id=None):
    owner = request.user
    conversation = (
        get_object_or_404(Conversation, id=conversation_id, owner=owner, dataset__owner=owner)
        if conversation_id
        else None
    )
    threads = (
        Conversation.objects.filter(owner=owner, dataset__owner=owner)
        if owner
        else Conversation.objects.none()
    )
    runs = (
        list(
            conversation.messages.filter(role="user", analysis_run__isnull=False)
            .select_related("analysis_run", "analysis_run__assistant_message")
            .order_by("-created_at", "-id")[:50]
        )
        if conversation
        else []
    )
    return render(
        request,
        "app/workspace.html",
        {
            "threads": threads,
            "conversation": conversation,
            "datasets": Dataset.objects.filter(owner=owner) if owner else Dataset.objects.none(),
            "thread_messages": reversed(runs),
        },
    )


@login_required
@require_POST
def new_thread(request):
    owner = request.user
    try:
        dataset = get_object_or_404(Dataset, id=request.POST.get("dataset_id"), owner=owner)
    except ValidationError:
        return JsonResponse({"error": "Select a valid dataset."}, status=400)
    title = request.POST.get("question", "New conversation").strip()[:100] or "New conversation"
    thread = Conversation.objects.create(dataset=dataset, owner=owner, title=title)
    return JsonResponse({"id": str(thread.id), "dataset_id": str(dataset.id)})
