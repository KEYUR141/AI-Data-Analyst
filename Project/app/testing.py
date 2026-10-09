from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client


def authenticated_client(**kwargs):
    client = Client(**kwargs)
    user = get_user_model().objects.create_user(
        username="test-" + uuid4().hex, password="Test-password-992!"
    )
    client.force_login(user)
    client.test_user = user
    return client
