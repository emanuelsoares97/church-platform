from decimal import Decimal
from django.test import TestCase

from events.models import Event, Registration, Participant


class EventModelTest(TestCase):
    """testa modelo event."""

    def test_event_slug_generation(self):
        """gera slug automaticamente."""
        event = Event.objects.create(
            title="Evento Teste",
            date="2024-12-25",
            location="Lisboa"
        )
        self.assertEqual(event.slug, "evento-teste")

    def test_event_slug_unique(self):
        """slug único para títulos iguais."""
        event1 = Event.objects.create(
            title="Evento Teste",
            date="2024-12-25",
            location="Lisboa"
        )
        event2 = Event.objects.create(
            title="Evento Teste",
            date="2024-12-26",
            location="Porto"
        )
        self.assertEqual(event1.slug, "evento-teste")
        self.assertEqual(event2.slug, "evento-teste-2")


class RegistrationModelTest(TestCase):
    """testa modelo registration."""

    def setUp(self):
        self.event = Event.objects.create(
            title="Evento Teste",
            date="2024-12-25",
            location="Lisboa",
            price=Decimal("10.00")
        )

    def test_registration_total_price(self):
        """calcula preço total corretamente."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=3
        )
        self.assertEqual(reg.total_price, Decimal("30.00"))

    def test_registration_mark_paid(self):
        """marca inscrição como paga."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        reg.mark_paid(True)
        self.assertTrue(reg.is_paid)
        self.assertIsNotNone(reg.paid_at)

        reg.mark_paid(False)
        self.assertFalse(reg.is_paid)
        self.assertIsNone(reg.paid_at)


class ParticipantModelTest(TestCase):
    """testa modelo participant."""

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
            phone="912345678"
        )

    def test_participant_mark_paid(self):
        """marca participante como pago."""
        part = Participant.objects.create(
            registration=self.reg,
            full_name="João Silva",
            ticket_code="TEST-001"
        )
        part.mark_paid(True)
        self.assertTrue(part.is_paid)
        self.assertIsNotNone(part.paid_at)

    def test_participant_mark_checked_in(self):
        """marca participante como check-in."""
        part = Participant.objects.create(
            registration=self.reg,
            full_name="João Silva",
            ticket_code="TEST-002"
        )
        part.mark_checked_in(True)
        self.assertTrue(part.checked_in)
        self.assertIsNotNone(part.checked_in_at)

        part.mark_checked_in(False)
        self.assertFalse(part.checked_in)
        self.assertIsNone(part.checked_in_at)