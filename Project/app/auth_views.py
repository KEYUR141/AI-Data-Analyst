from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import Conversation, Dataset


def claim_session(user, session_key):
    if session_key:
        with transaction.atomic():
            Dataset.objects.filter(owner__isnull=True, owner_session=session_key).update(owner=user)
            Conversation.objects.filter(
                owner__isnull=True, owner_session=session_key, dataset__owner=user
            ).update(owner=user)


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("app:home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        old_session = request.session.session_key
        user = form.save()
        claim_session(user, old_session)
        login(request, user)
        return redirect("app:home")
    return render(request, "registration/signup.html", {"form": form})


class AccountLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        claim_session(form.get_user(), self.request.session.session_key)
        return super().form_valid(form)
