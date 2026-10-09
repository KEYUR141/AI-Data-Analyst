from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .dataset_views import owned_dataset
from .models import AnalysisRun, Conversation, Message
from .services.charts import ChartError, build_chart
from .services.conversations import context_for, conversation_for, finish_run
from .services.execution import ExecutionError, execute_analysis
from .services.plan_schemas import AnalysisPlan, AnomalyPlan
from .services.planning import PlanningError, generate_plan
from .services.summaries import summarize


@login_required
@require_POST
def plan(request, dataset_id):
    dataset = owned_dataset(request, dataset_id)
    question = request.POST.get("question", "").strip()
    if not question or len(question) > 2000:
        return JsonResponse(
            {"error": "Provide a question between 1 and 2000 characters."}, status=400
        )
    thread_id = request.POST.get("conversation_id")
    conversation = (
        get_object_or_404(Conversation, id=thread_id, dataset=dataset, owner=request.user)
        if thread_id
        else conversation_for(dataset, request.user)
    )
    history = context_for(conversation)
    message = Message.objects.create(conversation=conversation, role="user", content=question)
    run = AnalysisRun.objects.create(user_message=message, status="running")
    try:
        result = generate_plan(question, dataset, history=history)
    except ImproperlyConfigured:
        finish_run(run, "LLM configuration is incomplete or invalid.", "failed")
        return JsonResponse({"error": "LLM configuration is incomplete or invalid."}, status=503)
    except PlanningError as exc:
        finish_run(run, str(exc), "failed")
        return JsonResponse({"error": str(exc)}, status=502)
    if isinstance(result, (AnalysisPlan, AnomalyPlan)):
        try:
            output = execute_analysis(result, dataset)
        except ExecutionError as exc:
            finish_run(run, str(exc), "failed", plan=result)
            return JsonResponse({"error": str(exc)}, status=422)
        try:
            output["chart"] = build_chart(
                result.chart if isinstance(result, AnalysisPlan) else None, output
            )
        except ChartError as exc:
            output["chart"] = None
            output["notes"].append(str(exc))
        output["summary"] = summarize(output)
        output["notes"].extend(output.get("method_notes", []))
        finish_run(run, output["summary"], "completed", output=output, plan=result)
        return JsonResponse(
            {"plan": result.model_dump(mode="json"), "executed": True, "result": output}
        )
    finish_run(run, result.question, "clarification", plan=result)
    return JsonResponse({"plan": result.model_dump(mode="json"), "executed": False})
