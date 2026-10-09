import json

from django.db import transaction
from django.utils import timezone

from app.models import AnalysisRun, Conversation, Message


def conversation_for(dataset, owner):
    with transaction.atomic():
        type(dataset).objects.select_for_update().get(pk=dataset.pk)
        conversation = Conversation.objects.filter(dataset=dataset, owner=owner).first()
        return conversation or Conversation.objects.create(
            dataset=dataset, owner=owner, title=dataset.original_name[:255]
        )


def context_for(conversation):
    history = []
    runs = (
        AnalysisRun.objects.filter(
            user_message__conversation=conversation, status__in=["completed", "clarification"]
        )
        .select_related("user_message", "assistant_message")
        .order_by("-created_at", "-id")[:6]
    )
    for run in reversed(list(runs)):
        entry = {
            "question": run.user_message.content[:2000],
            "response": run.assistant_message.content[:2000] if run.assistant_message else "",
            "plan": run.plan,
        }
        while history and len(json.dumps(history + [entry])) > 18000:
            history.pop(0)
        if len(json.dumps(history + [entry])) <= 18000:
            history.append(entry)
    return history


def finish_run(run, content, status, output=None, plan=None):
    with transaction.atomic():
        run.assistant_message = Message.objects.create(
            conversation=run.user_message.conversation, role="assistant", content=content
        )
        run.status = status
        run.completed_at = timezone.now()
        if plan:
            run.plan = plan.model_dump(mode="json")
            if plan.action == "analyze":
                run.chart_spec = plan.chart.model_dump() if plan.chart else {}
        if output:
            run.result = output
            run.executed_sql = output["sql"]
            run.duration_ms = output["duration_ms"]
        if status == "failed":
            run.error_message = content
        run.full_clean()
        run.save()
        Conversation.objects.filter(pk=run.user_message.conversation_id).update(
            updated_at=timezone.now()
        )
