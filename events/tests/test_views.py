import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from events.models import Event, Participant, Registration


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PublicEventViewsTest(TestCase):
    """Testa apenas as views públicas de eventos e inscrições."""

    def setUp(self):
        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

    def create_event(self, **kwargs):
        """Helper para criar eventos com defaults consistentes."""
        data = {
            "title": "Evento Público",
            "date": self.future_date,
            "location": "Lisboa",
            "price": Decimal("10.00"),
            "is_active": True,
            "is_archived": False,
            "registration_deadline": timezone.now() + timedelta(days=2),
        }
        data.update(kwargs)
        return Event.objects.create(**data)

    def valid_payload(self, **kwargs):
        """Dados válidos para envio de inscrição."""
        data = {
            "buyer_name": "João Silva",
            "buyer_email": "joao@example.com",
            "phone": "912345678",
            "ticket_qty": 2,
            "payment_method": "LOCAL",
            "participant_name": ["João Silva", "Maria Silva"],
        }
        data.update(kwargs)
        return data

    def test_event_list_mostra_apenas_eventos_publicos_validos(self):
        """A lista pública exclui inativos, arquivados e passados."""
        visible = self.create_event(title="Evento Visível")
        self.create_event(title="Evento Inativo", is_active=False)
        self.create_event(title="Evento Arquivado", is_archived=True)
        self.create_event(
            title="Evento Passado",
            date=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(reverse("events:event_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.title)
        self.assertNotContains(response, "Evento Inativo")
        self.assertNotContains(response, "Evento Arquivado")
        self.assertNotContains(response, "Evento Passado")

    def test_event_detail_disponivel_para_evento_publico_valido(self):
        """O detalhe abre normalmente para evento válido."""
        event = self.create_event(title="Evento Detalhe")

        response = self.client.get(reverse("events:event_detail", kwargs={"slug": event.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"].id, event.id)
        self.assertTrue(response.context["registration_open"])

    def test_event_detail_bloqueia_evento_inativo_arquivado_ou_passado(self):
        """Não permite abrir detalhe público para eventos fora das regras."""
        cases = [
            self.create_event(title="Inativo", is_active=False),
            self.create_event(title="Arquivado", is_archived=True),
            self.create_event(title="Passado", date=timezone.localdate() - timedelta(days=1)),
        ]

        for event in cases:
            with self.subTest(slug=event.slug):
                response = self.client.get(reverse("events:event_detail", kwargs={"slug": event.slug}))
                self.assertEqual(response.status_code, 404)

    def test_post_inscricao_bloqueado_quando_prazo_fechou(self):
        """Se prazo fechou, não cria inscrição e faz redirect para detalhe."""
        event = self.create_event(
            registration_deadline=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.post(
            reverse("events:event_detail", kwargs={"slug": event.slug}),
            self.valid_payload(),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events:event_detail", kwargs={"slug": event.slug}))
        self.assertEqual(Registration.objects.count(), 0)

    @patch("events.views.transaction.on_commit")
    def test_post_inscricao_valida_cria_registo_e_participantes(self, mock_on_commit):
        """Cria inscrição e participantes com ticket codes consistentes."""
        mock_on_commit.side_effect = lambda callback: None
        event = self.create_event(title="Evento com inscrição")

        response = self.client.post(
            reverse("events:event_detail", kwargs={"slug": event.slug}),
            self.valid_payload(),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Registration.objects.count(), 1)

        registration = Registration.objects.get(event=event)
        participants = list(registration.participants.order_by("id"))

        self.assertEqual(registration.ticket_qty, 2)
        self.assertEqual(len(participants), 2)
        self.assertEqual(participants[0].full_name, "João Silva")
        self.assertEqual(participants[1].full_name, "Maria Silva")
        self.assertTrue(participants[0].ticket_code.endswith("-P01"))
        self.assertTrue(participants[1].ticket_code.endswith("-P02"))

    @patch("events.views.transaction.on_commit")
    def test_post_com_numero_errado_de_participantes_nao_persiste_registo(self, mock_on_commit):
        """Se nomes não batem com quantidade, o registo é revertido."""
        mock_on_commit.side_effect = lambda callback: None
        event = self.create_event(title="Evento mismatch")

        payload = self.valid_payload(
            ticket_qty=3,
            participant_name=["João", "Maria"],
        )
        response = self.client.post(reverse("events:event_detail", kwargs={"slug": event.slug}), payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Registration.objects.count(), 0)
        self.assertContains(response, "Precisas preencher exatamente 3 nome(s) de participante")

    @patch("events.views.transaction.on_commit")
    def test_evento_gratuito_marca_inscricao_e_participantes_como_pagos(self, mock_on_commit):
        """No evento gratuito, pagamento fica fechado automaticamente."""
        mock_on_commit.side_effect = lambda callback: None
        event = self.create_event(title="Evento Gratuito", price=Decimal("0.00"))

        payload = self.valid_payload(
            ticket_qty=1,
            participant_name=["João Silva"],
        )
        payload.pop("payment_method")

        response = self.client.post(reverse("events:event_detail", kwargs={"slug": event.slug}), payload)

        self.assertEqual(response.status_code, 302)

        registration = Registration.objects.get(event=event)
        participant = registration.participants.get()

        self.assertTrue(registration.is_paid)
        self.assertIsNotNone(registration.paid_at)
        self.assertEqual(registration.paid_amount, registration.total_price)
        self.assertTrue(participant.is_paid)
        self.assertIsNotNone(participant.paid_at)

    def test_registration_success_mostra_dados_da_inscricao(self):
        """A página de sucesso carrega com inscrição válida."""
        event = self.create_event(title="Evento Sucesso")
        registration = Registration.objects.create(
            event=event,
            buyer_name="Ana",
            buyer_email="ana@example.com",
            phone="911111111",
            ticket_qty=1,
            payment_method="LOCAL",
        )
        Participant.objects.create(
            registration=registration,
            full_name="Ana",
            ticket_code="EVT-TEST-P01",
        )

        response = self.client.get(
            reverse(
                "events:registration_success",
                kwargs={"slug": event.slug, "public_id": registration.public_id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["registration"].id, registration.id)
        self.assertEqual(response.context["event"].id, event.id)
        self.assertEqual(len(response.context["participants"]), 1)

    def test_registration_success_404_com_public_id_invalido(self):
        """Se o public_id não existe para o evento, devolve 404."""
        event = self.create_event(title="Evento 404")
        Registration.objects.create(
            event=event,
            buyer_name="Teste",
            buyer_email="teste@example.com",
            phone="922222222",
            ticket_qty=1,
            payment_method="LOCAL",
        )

        response = self.client.get(
            reverse(
                "events:registration_success",
                kwargs={"slug": event.slug, "public_id": uuid.uuid4()},
            )
        )

        self.assertEqual(response.status_code, 404)