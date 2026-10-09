from django.contrib.auth import views as auth_views
from django.urls import path

from . import dataset_views, views, workspace_views
from .auth_views import AccountLoginView, signup
from .planning_views import plan
from .validation_views import validate_uploads

app_name = "app"
urlpatterns = [
    path("accounts/login/", AccountLoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", signup, name="signup"),
    path("datasets/<uuid:dataset_id>/plan/", plan, name="plan"),
    path("datasets/upload/", dataset_views.upload, name="upload"),
    path("datasets/<uuid:dataset_id>/", dataset_views.preview, name="preview"),
    path("datasets/<uuid:dataset_id>/delete/", dataset_views.remove, name="remove"),
    path("datasets/validate/", validate_uploads, name="validate_uploads"),
    path("", workspace_views.workspace, name="home"),
    path("threads/new/", workspace_views.new_thread, name="new_thread"),
    path("threads/<uuid:conversation_id>/", workspace_views.workspace, name="thread"),
    path("health/", views.health, name="health"),
    path("ready/", views.readiness, name="readiness"),
]
