from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from events.models import Event, Participant, Registration
from management.services.registration_ops import (
    BulkCheckinNotAllowed,
    ParticipantCheckinNotAllowed,
    checkin_all,
    mark_registration_paid_full,
    toggle_participant_checkin,
    toggle_participant_paid,
)


class RegistrationOpsServiceTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            title="Evento Ops",
            date=timezone.localdate() + timedelta(days=10),
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )
        self.registration = Registration.objects.create(
            event=self.event,
            buyer_name="Comprador",
            buyer_email="comprador@example.com",
            phone="912345678",
            ticket_qty=2,
            payment_method="LOCAL",
        )
        self.participant_1 = Participant.objects.create(
            registration=self.registration,
            full_name="P1",
            ticket_code="EVT-OPS-P01",
            is_paid=False,
            checked_in=False,
        )
        self.participant_2 = Participant.objects.create(
            registration=self.registration,
            full_name="P2",
            ticket_code="EVT-OPS-P02",
            is_paid=False,
            checked_in=False,
        )

    def test_mark_registration_paid_full_marca_registro_e_participantes(self):
        mark_registration_paid_full(self.registration)

        self.registration.refresh_from_db()
        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()

        self.assertTrue(self.registration.is_paid)
        self.assertEqual(self.registration.paid_amount, self.registration.total_price)
        self.assertTrue(self.participant_1.is_paid)
        self.assertTrue(self.participant_2.is_paid)

    def test_toggle_participant_paid_atualiza_registro(self):
        toggle_participant_paid(self.participant_1, new_value=True)
        self.registration.refresh_from_db()

        self.assertFalse(self.registration.is_paid)
        self.assertEqual(self.registration.paid_amount, Decimal("10.00"))

        toggle_participant_paid(self.participant_2, new_value=True)
        self.registration.refresh_from_db()

        self.assertTrue(self.registration.is_paid)
        self.assertEqual(self.registration.paid_amount, Decimal("20.00"))

    def test_toggle_participant_checkin_bloqueia_nao_pago(self):
        with self.assertRaises(ParticipantCheckinNotAllowed):
            toggle_participant_checkin(self.participant_1, new_value=True)

    def test_checkin_all_bloqueia_quando_existem_pendentes(self):
        self.participant_1.is_paid = True
        self.participant_1.paid_at = timezone.now()
        self.participant_1.save(update_fields=["is_paid", "paid_at"])

        with self.assertRaises(BulkCheckinNotAllowed):
            checkin_all(self.registration)

    def test_checkin_all_marca_todos_quando_pagos(self):
        for participant in (self.participant_1, self.participant_2):
            participant.is_paid = True
            participant.paid_at = timezone.now()
            participant.save(update_fields=["is_paid", "paid_at"])

        checkin_all(self.registration)

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()
        self.assertTrue(self.participant_1.checked_in)
        self.assertTrue(self.participant_2.checked_in)
