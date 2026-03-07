import uuid
from django.test import TestCase
from django.utils import timezone

from events.models import Registration
from events.views import make_ticket_code


class MakeTicketCodeTest(TestCase):
    """testa geração de códigos de bilhete."""

    def test_make_ticket_code(self):
        """gera código correto para participante."""
        # criar inscrição mock
        reg = Registration(
            public_id=uuid.uuid4(),
            created_at=timezone.now().replace(year=2024)
        )
        code = make_ticket_code(reg, 1)
        self.assertTrue(code.startswith("EVT-2024-"))
        self.assertTrue(code.endswith("-P01"))

        code2 = make_ticket_code(reg, 10)
        self.assertTrue(code2.endswith("-P10"))