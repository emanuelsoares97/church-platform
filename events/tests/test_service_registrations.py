from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from events.forms import RegistrationForm
from events.models import Event, Registration
from events.services.registrations import RegistrationCreationError, create_public_registration


class CreatePublicRegistrationServiceTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Evento Service",
            date=timezone.localdate() + timedelta(days=5),
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

    def make_form(self, **overrides):
        data = {
            "buyer_name": "Ana",
            "buyer_email": "ana@example.com",
            "phone": "912345678",
            "ticket_qty": 2,
            "payment_method": "LOCAL",
        }
        data.update(overrides)
        form = RegistrationForm(data=data)
        self.assertTrue(form.is_valid())
        return form

    @patch("events.services.registrations.transaction.on_commit")
    def test_create_public_registration_cria_inscricao_e_participantes(self, mock_on_commit):
        mock_on_commit.side_effect = lambda callback: None
        form = self.make_form()

        registration = create_public_registration(
            event=self.event,
            form=form,
            participant_names=["Ana", "Bruno"],
        )

        self.assertIsInstance(registration, Registration)
        self.assertEqual(registration.participants.count(), 2)
        participants = list(registration.participants.order_by("id"))
        self.assertTrue(participants[0].ticket_code.endswith("-P01"))
        self.assertTrue(participants[1].ticket_code.endswith("-P02"))

    @patch("events.services.registrations.transaction.on_commit")
    def test_create_public_registration_rollback_quando_participantes_invalidos(self, mock_on_commit):
        mock_on_commit.side_effect = lambda callback: None
        form = self.make_form(ticket_qty=3)

        with self.assertRaises(RegistrationCreationError):
            create_public_registration(
                event=self.event,
                form=form,
                participant_names=["Ana", "Bruno"],
            )

        self.assertEqual(Registration.objects.count(), 0)

    @patch("events.services.registrations.transaction.on_commit")
    def test_create_public_registration_evento_gratuito_fecha_pagamento(self, mock_on_commit):
        mock_on_commit.side_effect = lambda callback: None
        self.event.price = Decimal("0.00")
        self.event.save(update_fields=["price"])
        form = self.make_form(ticket_qty=1)

        registration = create_public_registration(
            event=self.event,
            form=form,
            participant_names=["Ana"],
        )

        participant = registration.participants.get()
        self.assertTrue(registration.is_paid)
        self.assertEqual(registration.paid_amount, registration.total_price)
        self.assertTrue(participant.is_paid)
