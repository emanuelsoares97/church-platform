from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from events.models import Event, Participant, Registration


class EventModelTest(TestCase):
    """Testa regras principais do modelo Event."""

    def test_gera_slug_automatico_e_unico(self):
        """Cria slug e garante sufixo quando já existe igual."""
        future_date = timezone.localdate() + timedelta(days=20)

        event_1 = Event.objects.create(
            title="Evento Teste",
            date=future_date,
            location="Lisboa",
        )
        event_2 = Event.objects.create(
            title="Evento Teste",
            date=future_date + timedelta(days=1),
            location="Porto",
        )

        self.assertEqual(event_1.slug, "evento-teste")
        self.assertEqual(event_2.slug, "evento-teste-2")

    def test_is_past_true_e_false(self):
        """Valida se o evento já passou com base na data."""
        past_event = Event.objects.create(
            title="Passado",
            date=timezone.localdate() - timedelta(days=1),
            location="Lisboa",
        )
        future_event = Event.objects.create(
            title="Futuro",
            date=timezone.localdate() + timedelta(days=1),
            location="Porto",
        )

        self.assertTrue(past_event.is_past())
        self.assertFalse(future_event.is_past())

    def test_is_registration_open_sem_prazo(self):
        """Sem prazo definido, as inscrições ficam abertas."""
        event = Event.objects.create(
            title="Sem prazo",
            date=timezone.localdate() + timedelta(days=10),
            location="Lisboa",
            registration_deadline=None,
        )

        self.assertTrue(event.is_registration_open())

    def test_is_registration_open_com_prazo(self):
        """Compara corretamente prazo futuro e passado."""
        open_event = Event.objects.create(
            title="Prazo aberto",
            date=timezone.localdate() + timedelta(days=10),
            location="Lisboa",
            registration_deadline=timezone.now() + timedelta(hours=2),
        )
        closed_event = Event.objects.create(
            title="Prazo fechado",
            date=timezone.localdate() + timedelta(days=10),
            location="Porto",
            registration_deadline=timezone.now() - timedelta(minutes=1),
        )

        self.assertTrue(open_event.is_registration_open())
        self.assertFalse(closed_event.is_registration_open())

    def test_can_accept_registrations_so_quando_todas_regras_passam(self):
        """Aceita inscrições apenas quando estado e datas estão válidos."""
        base = Event.objects.create(
            title="Evento válido",
            date=timezone.localdate() + timedelta(days=5),
            location="Lisboa",
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=1),
        )
        self.assertTrue(base.can_accept_registrations())

        scenarios = [
            {
                "title": "Inativo",
                "kwargs": {"is_active": False},
            },
            {
                "title": "Arquivado",
                "kwargs": {"is_archived": True},
            },
            {
                "title": "Passado",
                "kwargs": {"date": timezone.localdate() - timedelta(days=1)},
            },
            {
                "title": "Prazo fechado",
                "kwargs": {"registration_deadline": timezone.now() - timedelta(minutes=1)},
            },
        ]

        for scenario in scenarios:
            with self.subTest(caso=scenario["title"]):
                data = {
                    "title": f"Evento {scenario['title']}",
                    "date": timezone.localdate() + timedelta(days=5),
                    "location": "Lisboa",
                    "is_active": True,
                    "is_archived": False,
                    "registration_deadline": timezone.now() + timedelta(days=1),
                }
                data.update(scenario["kwargs"])
                event = Event.objects.create(**data)
                self.assertFalse(event.can_accept_registrations())


class RegistrationModelTest(TestCase):
    """Testa consistência do modelo Registration."""

    def setUp(self):
        self.event = Event.objects.create(
            title="Evento Pago",
            date=timezone.localdate() + timedelta(days=15),
            location="Lisboa",
            price=Decimal("10.00"),
        )

    def test_total_price_e_is_fully_paid(self):
        """Calcula o total e valida estado de pagamento completo."""
        registration = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=3,
            paid_amount=Decimal("20.00"),
        )

        self.assertEqual(registration.total_price, Decimal("30.00"))
        self.assertFalse(registration.is_fully_paid)

        registration.paid_amount = Decimal("30.00")
        self.assertTrue(registration.is_fully_paid)

    def test_mark_paid_alterna_estado(self):
        """Atualiza flags de pagamento da inscrição."""
        registration = Registration.objects.create(
            event=self.event,
            buyer_name="Ana Silva",
            buyer_email="ana@example.com",
            phone="923456789",
            ticket_qty=1,
        )

        registration.mark_paid(True)
        self.assertTrue(registration.is_paid)
        self.assertIsNotNone(registration.paid_at)

        registration.mark_paid(False)
        self.assertFalse(registration.is_paid)
        self.assertIsNone(registration.paid_at)


class ParticipantModelTest(TestCase):
    """Testa regras úteis do modelo Participant."""

    def setUp(self):
        event = Event.objects.create(
            title="Evento Participantes",
            date=timezone.localdate() + timedelta(days=10),
            location="Lisboa",
        )
        self.registration = Registration.objects.create(
            event=event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1,
        )

    def test_mark_paid_altera_campos(self):
        """Marca e desmarca pagamento do participante."""
        participant = Participant.objects.create(
            registration=self.registration,
            full_name="Participante 1",
            ticket_code="TEST-001",
        )

        participant.mark_paid(True)
        self.assertTrue(participant.is_paid)
        self.assertIsNotNone(participant.paid_at)

        participant.mark_paid(False)
        self.assertFalse(participant.is_paid)
        self.assertIsNone(participant.paid_at)

    def test_mark_checked_in_altera_campos(self):
        """Marca e desmarca check-in do participante."""
        participant = Participant.objects.create(
            registration=self.registration,
            full_name="Participante 2",
            ticket_code="TEST-002",
        )

        participant.mark_checked_in(True)
        self.assertTrue(participant.checked_in)
        self.assertIsNotNone(participant.checked_in_at)

        participant.mark_checked_in(False)
        self.assertFalse(participant.checked_in)
        self.assertIsNone(participant.checked_in_at)