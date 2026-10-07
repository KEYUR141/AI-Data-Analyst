from dataclasses import asdict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.validation import CSVLimits, validate_csv


@require_POST
def validate_uploads(request):
    """Validate a bounded batch; no files or metadata are persisted yet."""
    files = request.FILES.getlist("files")
    if not files:
        return JsonResponse({"error": "Provide CSV uploads in the files field."}, status=400)
    if len(files) > settings.CSV_MAX_FILES:
        return JsonResponse({"error": "Too many files in one request."}, status=400)
    limits = CSVLimits(
        max_bytes=settings.CSV_MAX_BYTES,
        max_rows=settings.CSV_MAX_ROWS,
        max_columns=settings.CSV_MAX_COLUMNS,
        preview_rows=settings.CSV_PREVIEW_ROWS,
    )
    results = []
    for upload in files:
        try:
            result = validate_csv(upload, limits)
        except ValidationError as exc:
            results.append(
                {
                    "filename": upload.name,
                    "valid": False,
                    "error": {"code": exc.code, "message": exc.messages[0]},
                }
            )
        else:
            results.append({"filename": upload.name, "valid": True, **asdict(result)})
    return JsonResponse({"files": results})
