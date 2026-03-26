from django.test import TestCase
from django.urls import reverse


class HealthcheckViewTests(TestCase):
    def test_healthcheck_retorna_status_ok(self):
        response = self.client.get(reverse("core:healthcheck"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
