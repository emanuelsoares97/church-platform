from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from events.models import Event, Participant, Registration
from management.constants import GROUP_LEADERSHIP, GROUP_RECEPTION


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class RegistrationOperationsPermissionsTest(TestCase):
    """Testa permissões para operações de inscrições e participantes."""

    def setUp(self):
        """Cria utilizadores, grupos, evento e inscrição."""
        self.leadership_group = Group.objects.create(name=GROUP_LEADERSHIP)
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)

        self.leadership_user = User.objects.create_user(
            username="lider", password="pass123"
        )
        self.leadership_user.groups.add(self.leadership_group)

        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.no_group_user = User.objects.create_user(
            username="sem_grupo", password="pass123"
        )

        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

        self.event = Event.objects.create(
            title="Evento Teste",
            date=self.future_date,
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

        self.registration = Registration.objects.create(
            event=self.event,
            buyer_name="Comprador",
            buyer_email="comp@test.com",
            phone="912345678",
            ticket_qty=2,
            payment_method="LOCAL",
        )

        self.participant_1 = Participant.objects.create(
            registration=self.registration,
            full_name="Participante 1",
            ticket_code="EVT-00001-P01",
            is_paid=False,
            checked_in=False,
        )

        self.participant_2 = Participant.objects.create(
            registration=self.registration,
            full_name="Participante 2",
            ticket_code="EVT-00001-P02",
            is_paid=False,
            checked_in=False,
        )

    def test_mark_registration_paid_full_anon_bloqueado(self):
        """Utilizador anónimo não pode marcar pagamento."""
        response = self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 302)

    def test_mark_registration_paid_full_sem_grupo_bloqueado(self):
        """Utilizador sem grupo não pode marcar pagamento."""
        self.client.login(username="sem_grupo", password="pass123")
        response = self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_mark_registration_paid_full_reception_pode(self):
        """Receção pode marcar inscrição como paga."""
        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 302)
        self.registration.refresh_from_db()
        self.assertTrue(self.registration.is_paid)

    def test_mark_registration_paid_full_leadership_pode(self):
        """Liderança pode marcar inscrição como paga."""
        self.client.login(username="lider", password="pass123")
        response = self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 302)
        self.registration.refresh_from_db()
        self.assertTrue(self.registration.is_paid)

    def test_mark_registration_paid_full_marca_todos_participantes(self):
        """Marcar inscrição como paga marca todos os participantes como pagos."""
        self.client.login(username="rececao", password="pass123")
        self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()

        self.assertTrue(self.participant_1.is_paid)
        self.assertTrue(self.participant_2.is_paid)
        self.assertIsNotNone(self.participant_1.paid_at)
        self.assertIsNotNone(self.participant_2.paid_at)

    def test_mark_registration_paid_full_preenche_paid_amount_e_paid_at(self):
        """Marcar inscrição como paga preenche paid_amount e paid_at."""
        self.client.login(username="rececao", password="pass123")
        before = timezone.now()
        self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": self.registration.id})
        )
        after = timezone.now()

        self.registration.refresh_from_db()
        self.assertEqual(self.registration.paid_amount, self.registration.total_price)
        self.assertLess(before, self.registration.paid_at)
        self.assertLess(self.registration.paid_at, after)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ToggleParticipantPaidTest(TestCase):
    """Testa o toggle de pagamento de participante individual."""

    def setUp(self):
        """Cria utilizadores, grupos e evento com inscrição."""
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)

        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

        self.event = Event.objects.create(
            title="Evento Pago",
            date=self.future_date,
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

        self.registration = Registration.objects.create(
            event=self.event,
            buyer_name="Comprador",
            buyer_email="comp@test.com",
            phone="912345678",
            ticket_qty=1,
            payment_method="LOCAL",
        )

        self.participant = Participant.objects.create(
            registration=self.registration,
            full_name="Participante",
            ticket_code="EVT-00001-P01",
            is_paid=False,
            checked_in=False,
        )

    def test_toggle_participant_paid_marca_como_pago(self):
        """Toggle com value=1 marca participante como pago."""
        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": self.participant.id}),
            {"value": "1"},
        )

        self.assertEqual(response.status_code, 302)
        self.participant.refresh_from_db()
        self.assertTrue(self.participant.is_paid)
        self.assertIsNotNone(self.participant.paid_at)

    def test_toggle_participant_paid_marca_como_nao_pago(self):
        """Toggle com value=0 marca participante como não pago."""
        self.participant.is_paid = True
        self.participant.paid_at = timezone.now()
        self.participant.save()

        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": self.participant.id}),
            {"value": "0"},
        )

        self.assertEqual(response.status_code, 302)
        self.participant.refresh_from_db()
        self.assertFalse(self.participant.is_paid)
        self.assertIsNone(self.participant.paid_at)

    def test_toggle_participant_paid_atualiza_registration_paid_amount(self):
        """Toggle de participante individual atualiza paid_amount da inscrição."""
        self.client.login(username="rececao", password="pass123")
        self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": self.participant.id}),
            {"value": "1"},
        )

        self.registration.refresh_from_db()
        self.assertEqual(self.registration.paid_amount, Decimal("10.00"))

    def test_toggle_participant_paid_toggle_multiplos_atualiza_status_registration(self):
        """Toggle de múltiplos participantes atualiza is_paid da inscrição."""
        self.registration.ticket_qty = 2
        self.registration.save()

        participant_2 = Participant.objects.create(
            registration=self.registration,
            full_name="Participante 2",
            ticket_code="EVT-00001-P02",
            is_paid=False,
        )

        self.client.login(username="rececao", password="pass123")

        # Marcar primeiro participante como pago
        self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": self.participant.id}),
            {"value": "1"},
        )
        self.registration.refresh_from_db()
        self.assertFalse(self.registration.is_paid)

        # Marcar segundo como pago
        self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": participant_2.id}),
            {"value": "1"},
        )
        self.registration.refresh_from_db()
        self.assertTrue(self.registration.is_paid)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ToggleParticipantCheckinTest(TestCase):
    """Testa o toggle de check-in de participante."""

    def setUp(self):
        """Cria evento com evento pago."""
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)
        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

        self.paid_event = Event.objects.create(
            title="Evento Pago",
            date=self.future_date,
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

        self.free_event = Event.objects.create(
            title="Evento Gratuito",
            date=self.future_date,
            location="Porto",
            price=Decimal("0.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

    def test_toggle_checkin_nao_pago_em_evento_pago_bloqueado(self):
        """Check-in bloqueado se participante não pagou em evento pago."""
        registration = Registration.objects.create(
            event=self.paid_event,
            buyer_name="Comprador",
            buyer_email="comp@test.com",
            phone="912345678",
            ticket_qty=1,
            payment_method="LOCAL",
        )

        participant = Participant.objects.create(
            registration=registration,
            full_name="Não Pago",
            ticket_code="EVT-00001-P01",
            is_paid=False,
        )

        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "1"},
        )

        self.assertEqual(response.status_code, 302)
        participant.refresh_from_db()
        self.assertFalse(participant.checked_in)

    def test_toggle_checkin_pago_em_evento_pago_funciona(self):
        """Check-in funciona se participante pagou em evento pago."""
        registration = Registration.objects.create(
            event=self.paid_event,
            buyer_name="Comprador",
            buyer_email="comp@test.com",
            phone="912345678",
            ticket_qty=1,
            payment_method="LOCAL",
        )

        participant = Participant.objects.create(
            registration=registration,
            full_name="Pago",
            ticket_code="EVT-00001-P01",
            is_paid=True,
            paid_at=timezone.now(),
        )

        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "1"},
        )

        self.assertEqual(response.status_code, 302)
        participant.refresh_from_db()
        self.assertTrue(participant.checked_in)
        self.assertIsNotNone(participant.checked_in_at)

    def test_toggle_checkin_evento_gratuito_sem_bloqueio(self):
        """Check-in funciona em evento gratuito sem exigir pagamento."""
        registration = Registration.objects.create(
            event=self.free_event,
            buyer_name="Visitante",
            buyer_email="visit@test.com",
            phone="987654321",
            ticket_qty=1,
            payment_method="FREE",
        )

        participant = Participant.objects.create(
            registration=registration,
            full_name="Visitante",
            ticket_code="EVT-00002-P01",
            is_paid=False,
        )

        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "1"},
        )

        self.assertEqual(response.status_code, 302)
        participant.refresh_from_db()
        self.assertTrue(participant.checked_in)

    def test_toggle_checkin_uncheckin_limpa_timestamp(self):
        """Remover check-in limpa o checked_in_at."""
        registration = Registration.objects.create(
            event=self.free_event,
            buyer_name="Visitante",
            buyer_email="visit@test.com",
            phone="987654321",
            ticket_qty=1,
            payment_method="FREE",
        )

        participant = Participant.objects.create(
            registration=registration,
            full_name="Visitante",
            ticket_code="EVT-00002-P01",
            checked_in=True,
            checked_in_at=timezone.now(),
        )

        self.client.login(username="rececao", password="pass123")
        self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "0"},
        )

        participant.refresh_from_db()
        self.assertFalse(participant.checked_in)
        self.assertIsNone(participant.checked_in_at)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class CheckinAllTest(TestCase):
    """Testa check-in em massa de todos os participantes da inscrição."""

    def setUp(self):
        """Cria evento e inscrição com múltiplos participantes."""
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)
        self.reception_user = User.objects.create_user(
            username="rececao", password="pass123"
        )
        self.reception_user.groups.add(self.reception_group)

        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

        self.event = Event.objects.create(
            title="Evento Grupo",
            date=self.future_date,
            location="Lisboa",
            price=Decimal("10.00"),
            is_active=True,
            is_archived=False,
            registration_deadline=timezone.now() + timedelta(days=2),
        )

        self.registration = Registration.objects.create(
            event=self.event,
            buyer_name="Grupo",
            buyer_email="grupo@test.com",
            phone="912345678",
            ticket_qty=3,
            payment_method="LOCAL",
        )

        self.participant_1 = Participant.objects.create(
            registration=self.registration,
            full_name="P1",
            ticket_code="EVT-00001-P01",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=False,
        )

        self.participant_2 = Participant.objects.create(
            registration=self.registration,
            full_name="P2",
            ticket_code="EVT-00001-P02",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=False,
        )

        self.participant_3 = Participant.objects.create(
            registration=self.registration,
            full_name="P3",
            ticket_code="EVT-00001-P03",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=False,
        )

    def test_checkin_all_marca_todos_participantes(self):
        """Checkin all marca todos os participantes como checked-in."""
        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 302)

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()
        self.participant_3.refresh_from_db()

        self.assertTrue(self.participant_1.checked_in)
        self.assertTrue(self.participant_2.checked_in)
        self.assertTrue(self.participant_3.checked_in)

    def test_checkin_all_bloqueado_se_alguem_nao_pagou(self):
        """Checkin all bloqueado se há pagamentos pendentes."""
        self.participant_3.is_paid = False
        self.participant_3.paid_at = None
        self.participant_3.save()

        self.client.login(username="rececao", password="pass123")
        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": self.registration.id})
        )

        self.assertEqual(response.status_code, 302)

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()
        self.participant_3.refresh_from_db()

        self.assertFalse(self.participant_1.checked_in)
        self.assertFalse(self.participant_2.checked_in)
        self.assertFalse(self.participant_3.checked_in)

    def test_checkin_all_preenche_timestamp_para_todos(self):
        """Checkin all preenche checked_in_at para todos."""
        self.client.login(username="rececao", password="pass123")
        before = timezone.now()
        self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": self.registration.id})
        )
        after = timezone.now()

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()
        self.participant_3.refresh_from_db()

        self.assertIsNotNone(self.participant_1.checked_in_at)
        self.assertIsNotNone(self.participant_2.checked_in_at)
        self.assertIsNotNone(self.participant_3.checked_in_at)

        self.assertLess(before, self.participant_1.checked_in_at)
        self.assertLess(before, self.participant_2.checked_in_at)
        self.assertLess(before, self.participant_3.checked_in_at)

    def test_checkin_all_preserva_ja_checkin(self):
        """Checkin all preserva participantes que já têm check-in."""
        first_time = timezone.now() - timedelta(hours=1)
        self.participant_1.checked_in = True
        self.participant_1.checked_in_at = first_time
        self.participant_1.save()

        self.client.login(username="rececao", password="pass123")
        self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": self.registration.id})
        )

        self.participant_1.refresh_from_db()
        self.participant_2.refresh_from_db()

        self.assertEqual(self.participant_1.checked_in_at, first_time)
        self.assertTrue(self.participant_2.checked_in)
        self.assertIsNotNone(self.participant_2.checked_in_at)
