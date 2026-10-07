from django.core.exceptions import ImproperlyConfigured
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .dataset_views import owned_dataset
from .services.charts import ChartError, build_chart
from .services.execution import ExecutionError, execute_analysis
from .services.plan_schemas import AnalysisPlan
from .services.planning import PlanningError, generate_plan


@require_POST
def plan(request, dataset_id):
    dataset = owned_dataset(request, dataset_id)
    question = request.POST.get("question", "").strip()
    if not question or len(question) > 2000:
        return JsonResponse(
            {"error": "Provide a question between 1 and 2000 characters."}, status=400
        )
    try:
        result = generate_plan(question, dataset)
    except ImproperlyConfigured:
        return JsonResponse({"error": "LLM configuration is incomplete or invalid."}, status=503)
    except PlanningError as exc:
        return JsonResponse({"error": str(exc)}, status=502)
    if isinstance(result, AnalysisPlan):
        try:
            output = execute_analysis(result, dataset)
        except ExecutionError as exc:
            return JsonResponse({"error": str(exc)}, status=422)
        try:
            output["chart"] = build_chart(result.chart, output)
        except ChartError as exc:
            output["chart"] = None
            output["notes"].append(str(exc))
        return JsonResponse(
            {"plan": result.model_dump(mode="json"), "executed": True, "result": output}
        )
    return JsonResponse({"plan": result.model_dump(mode="json"), "executed": False})
