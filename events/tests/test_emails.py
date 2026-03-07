from io import BytesIO
from unittest.mock import patch, MagicMock

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from events.models import Event, Registration, Participant
from events.services.emails import send_registration_tickets_email, _make_qr_png


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

    @patch('events.services.emails.EmailMultiAlternatives.send')
    def test_send_registration_tickets_email(self, mock_send):
        """envia email com bilhete."""
        send_registration_tickets_email(self.reg.id)
        self.assertEqual(mock_send.call_count, 1)

    @patch('events.services.emails.EmailMultiAlternatives.send')
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

    @patch('events.services.emails.EmailMultiAlternatives.send')
    @patch('events.services.emails._attach_inline_file_image')
    def test_send_registration_tickets_email_with_banner(self, mock_attach, mock_send):
        """envia email com banner se existir."""
        # adicionar banner ao evento
        self.event.banner_image.save('banner.png', ContentFile(b'test image data'), save=True)
        
        send_registration_tickets_email(self.reg.id)
        mock_attach.assert_called_once()
        mock_send.assert_called_once()

    def test_make_qr_png(self):
        """gera png do qr code."""
        png_data = _make_qr_png("test data")
        self.assertIsInstance(png_data, bytes)
        self.assertGreater(len(png_data), 0)
        
        # verificar se é png válido
        buf = BytesIO(png_data)
        # se não lançar erro, é png válido
        from PIL import Image
        img = Image.open(buf)
        self.assertEqual(img.format, "PNG")