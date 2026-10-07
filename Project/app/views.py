import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def home(request):
    from .models import Dataset

    datasets = (
        Dataset.objects.filter(owner_session=request.session.session_key)
        if request.session.session_key
        else []
    )
    return render(request, "app/home.html", {"datasets": datasets})


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def readiness(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.warning("Database readiness check failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
