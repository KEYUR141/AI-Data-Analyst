from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase
from django.urls import reverse


class FoundationTests(SimpleTestCase):
    def test_home(self):
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_health_without_database(self):
        self.assertEqual(self.client.get(reverse("app:health")).json(), {"status": "ok"})

    @patch("app.views.connection")
    def test_unavailable_database(self, connection):
        connection.cursor.side_effect = OperationalError("private details")
        response = self.client.get(reverse("app:readiness"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    @patch("app.views.connection")
    def test_ready_database(self, connection):
        self.assertEqual(self.client.get(reverse("app:readiness")).status_code, 200)
        connection.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            "SELECT 1"
        )
