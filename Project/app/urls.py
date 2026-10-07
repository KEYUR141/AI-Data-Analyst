from django.urls import path

from . import dataset_views, views
from .planning_views import plan
from .validation_views import validate_uploads

app_name = "app"
urlpatterns = [
    path("datasets/<uuid:dataset_id>/plan/", plan, name="plan"),
    path("datasets/upload/", dataset_views.upload, name="upload"),
    path("datasets/<uuid:dataset_id>/", dataset_views.preview, name="preview"),
    path("datasets/<uuid:dataset_id>/delete/", dataset_views.remove, name="remove"),
    path("datasets/validate/", validate_uploads, name="validate_uploads"),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("ready/", views.readiness, name="readiness"),
]
