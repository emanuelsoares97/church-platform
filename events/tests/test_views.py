from decimal import Decimal
from django.contrib.auth.models import Group, User
from django.test import TestCase, Client
from django.urls import reverse

from events.models import Event, Registration, Participant


class PublicViewsTest(TestCase):
    """testa views públicas."""

    def setUp(self):
        self.client = Client()
        self.event = Event.objects.create(
            title="Evento Público",
            date="2024-12-25",
            location="Lisboa",
            is_active=True
        )

    def test_event_list(self):
        """lista eventos ativos."""
        response = self.client.get(reverse("events:event_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Público")

    def test_event_detail(self):
        """detalhe do evento."""
        response = self.client.get(reverse("events:event_detail", kwargs={"slug": self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Público")

    def test_event_detail_post_valid(self):
        """inscrição válida cria registo e participantes."""
        data = {
            "buyer_name": "João Silva",
            "buyer_email": "joao@example.com",
            "phone": "912345678",
            "ticket_qty": 2,
            "payment_method": "LOCAL",
            "participant_name": ["João Silva", "Maria Silva"],
        }
        response = self.client.post(reverse("events:event_detail", kwargs={"slug": self.event.slug}), data)
        self.assertEqual(response.status_code, 302)  # redirect to success
        self.assertEqual(Registration.objects.count(), 1)
        reg = Registration.objects.first()
        self.assertEqual(reg.participants.count(), 2)
        self.assertTrue(all(p.ticket_code.startswith("EVT-") for p in reg.participants.all()))

    def test_event_detail_post_invalid_form(self):
        """formulário inválido volta à página com erros."""
        data = {
            "buyer_name": "",
            "buyer_email": "invalid-email",
            "phone": "912345678",
            "ticket_qty": 1,
            "payment_method": "LOCAL",
            "participant_name": ["João"],
        }
        response = self.client.post(reverse("events:event_detail", kwargs={"slug": self.event.slug}), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Há campos inválidos")

    def test_event_detail_post_wrong_participant_count(self):
        """número errado de participantes volta à página com erro."""
        data = {
            "buyer_name": "João Silva",
            "buyer_email": "joao@example.com",
            "phone": "912345678",
            "ticket_qty": 3,
            "payment_method": "LOCAL",
            "participant_name": ["João", "Maria"],  # só 2 em vez de 3
        }
        response = self.client.post(reverse("events:event_detail", kwargs={"slug": self.event.slug}), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Precisas preencher exatamente 3 nome(s)")
        self.assertEqual(Registration.objects.count(), 0)

    def test_event_detail_free_event(self):
        """evento gratuito marca tudo como pago automaticamente."""
        free_event = Event.objects.create(
            title="Evento Gratuito",
            date="2024-12-25",
            location="Lisboa",
            price=Decimal("0.00"),
            is_active=True
        )
        data = {
            "buyer_name": "João Silva",
            "buyer_email": "joao@example.com",
            "phone": "912345678",
            "ticket_qty": 1,
            "payment_method": "LOCAL",
            "participant_name": ["João Silva"],
        }
        response = self.client.post(reverse("events:event_detail", kwargs={"slug": free_event.slug}), data)
        self.assertEqual(response.status_code, 302)
        reg = Registration.objects.get(event=free_event)
        self.assertTrue(reg.is_paid)
        self.assertTrue(reg.participants.first().is_paid)


class ManagementViewsTest(TestCase):
    """testa views de gestão."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="manager", password="pass")
        group = Group.objects.create(name="Gestão Eventos")
        self.user.groups.add(group)
        self.client.login(username="manager", password="pass")

        self.event = Event.objects.create(
            title="Evento Gestão",
            date="2024-12-25",
            location="Lisboa"
        )

    def test_dashboard_home_requires_login(self):
        """dashboard requer login."""
        self.client.logout()
        response = self.client.get(reverse("management:home"))
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_dashboard_home(self):
        """dashboard acessível com permissão."""
        response = self.client.get(reverse("management:home"))
        self.assertEqual(response.status_code, 200)

    def test_event_registrations(self):
        """lista inscrições do evento."""
        response = self.client.get(reverse("management:event_regs", kwargs={"event_id": self.event.id}))
        self.assertEqual(response.status_code, 200)

    def test_scan_page(self):
        """página do scanner."""
        response = self.client.get(reverse("management:scan"))
        self.assertEqual(response.status_code, 200)

    def test_mark_registration_paid_full(self):
        """marca inscrição completa como paga."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        Participant.objects.create(registration=reg, full_name="João", ticket_code="T1")
        Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2")
        
        response = self.client.post(reverse("management:mark_registration_paid_full", kwargs={"reg_id": reg.id}))
        self.assertEqual(response.status_code, 302)
        reg.refresh_from_db()
        self.assertTrue(reg.is_paid)
        self.assertTrue(all(p.is_paid for p in reg.participants.all()))

    def test_toggle_participant_paid(self):
        """alterna pagamento de participante."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1")
        
        # marcar como pago
        response = self.client.post(reverse("management:toggle_participant_paid", kwargs={"participant_id": part.id}), {"value": "1"})
        self.assertEqual(response.status_code, 302)
        part.refresh_from_db()
        self.assertTrue(part.is_paid)
        
        # desmarcar
        response = self.client.post(reverse("management:toggle_participant_paid", kwargs={"participant_id": part.id}), {"value": "0"})
        self.assertEqual(response.status_code, 302)
        part.refresh_from_db()
        self.assertFalse(part.is_paid)

    def test_toggle_participant_checkin_paid(self):
        """check-in só funciona se pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        
        response = self.client.post(reverse("management:toggle_participant_checkin", kwargs={"participant_id": part.id}), {"value": "1"})
        self.assertEqual(response.status_code, 302)
        part.refresh_from_db()
        self.assertTrue(part.checked_in)

    def test_toggle_participant_checkin_unpaid(self):
        """check-in bloqueado se não pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=False)
        
        response = self.client.post(reverse("management:toggle_participant_checkin", kwargs={"participant_id": part.id}), {"value": "1"})
        self.assertEqual(response.status_code, 302)
        part.refresh_from_db()
        self.assertFalse(part.checked_in)

    def test_checkin_all_paid(self):
        """check-in de todos se todos pagos."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        p1 = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        p2 = Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2", is_paid=True)
        
        response = self.client.post(reverse("management:checkin_all", kwargs={"reg_id": reg.id}))
        self.assertEqual(response.status_code, 302)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertTrue(p1.checked_in)
        self.assertTrue(p2.checked_in)

    def test_checkin_all_unpaid(self):
        """check-in de todos bloqueado se algum não pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        p1 = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        p2 = Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2", is_paid=False)
        
        response = self.client.post(reverse("management:checkin_all", kwargs={"reg_id": reg.id}))
        self.assertEqual(response.status_code, 302)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertFalse(p1.checked_in)
        self.assertFalse(p2.checked_in)

    def test_scan_checkin_api_valid(self):
        """check-in via api do scanner."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        
        response = self.client.post(reverse("management:scan_checkin_api"), {"ticket_code": "T1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["status"], "checked_in")
        part.refresh_from_db()
        self.assertTrue(part.checked_in)

    def test_scan_checkin_api_not_found(self):
        """código inválido retorna erro."""
        response = self.client.post(reverse("management:scan_checkin_api"), {"ticket_code": "INVALID"})
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["status"], "not_found")

    def test_scan_checkin_api_unpaid(self):
        """check-in bloqueado se não pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=False)
        
        response = self.client.post(reverse("management:scan_checkin_api"), {"ticket_code": "T1"})
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["status"], "payment_pending")

    def test_ticket_lookup(self):
        """busca participante por código."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1")
        
        response = self.client.get(reverse("management:ticket_lookup", kwargs={"ticket_code": "T1"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "João")

    def test_registration_group(self):
        """página do grupo de inscrição."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        p1 = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True, checked_in=True)
        p2 = Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2", is_paid=False, checked_in=False)
        
        response = self.client.get(reverse("management:registration_group", kwargs={"reg_id": reg.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "João Silva")

    def test_toggle_participant_paid_ajax(self):
        """alterna pagamento de participante via AJAX."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1")
        
        # marcar como pago via AJAX
        response = self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": part.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        part.refresh_from_db()
        self.assertTrue(part.is_paid)

    def test_toggle_participant_checkin_ajax_paid(self):
        """check-in via AJAX só funciona se pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        
        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": part.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        part.refresh_from_db()
        self.assertTrue(part.checked_in)

    def test_toggle_participant_checkin_ajax_unpaid(self):
        """check-in via AJAX bloqueado se não pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        part = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=False)
        
        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": part.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        part.refresh_from_db()
        self.assertFalse(part.checked_in)

    def test_checkin_all_ajax_paid(self):
        """check-in de todos via AJAX se todos pagos."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        p1 = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        p2 = Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2", is_paid=True)
        
        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": reg.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertTrue(p1.checked_in)
        self.assertTrue(p2.checked_in)

    def test_checkin_all_ajax_unpaid(self):
        """check-in de todos via AJAX bloqueado se algum não pago."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=2
        )
        p1 = Participant.objects.create(registration=reg, full_name="João", ticket_code="T1", is_paid=True)
        p2 = Participant.objects.create(registration=reg, full_name="Maria", ticket_code="T2", is_paid=False)
        
        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": reg.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertFalse(p1.checked_in)
        self.assertFalse(p2.checked_in)


class RegistrationViewsTest(TestCase):
    """testa views de inscrição."""

    def setUp(self):
        self.client = Client()
        self.event = Event.objects.create(
            title="Evento Inscrição",
            date="2024-12-25",
            location="Lisboa",
            price=Decimal("10.00")
        )

    def test_registration_success(self):
        """página de sucesso de inscrição."""
        reg = Registration.objects.create(
            event=self.event,
            buyer_name="João Silva",
            buyer_email="joao@example.com",
            phone="912345678",
            ticket_qty=1
        )
        response = self.client.get(
            reverse("events:registration_success", kwargs={"slug": self.event.slug, "public_id": reg.public_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Evento Inscrição")