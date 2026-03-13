from io import BytesIO
from unittest.mock import patch, MagicMock

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from events.models import Event, Registration, Participant
from events.services.emails import send_registration_tickets_email


class EmailServiceTest(TestCase):
    """testa serviço de envio de emails."""

    def setUp(self):
        self.event = Event.objects.create(
            title="Evento Teste",
            date="2024-12-25",
            location="Lisboa"
        )
        self.reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        self.part = Participant.objects.create(
            registration=self.reg,
            full_name="João Silva",
            ticket_code="TEST-001"
        )

    @patch('events.services.emails._send_email_resend')
    def test_send_registration_tickets_email(self, mock_send):
        """envia email com bilhete."""
        send_registration_tickets_email(self.reg.id)
        self.assertEqual(mock_send.call_count, 1)

    @patch('events.services.emails._send_email_resend')
    def test_send_registration_tickets_email_no_participants(self, mock_send):
        """não envia email se não houver participantes."""
        reg_empty = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=0
        )
        send_registration_tickets_email(reg_empty.id)
        mock_send.assert_not_called()

    @patch('events.services.emails._send_email_resend')
    def test_send_registration_tickets_email_with_banner(self, mock_send):
        """envia email mesmo com banner no evento."""
        send_registration_tickets_email(self.reg.id)
        mock_send.assert_called_once()