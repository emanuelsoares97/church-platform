from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from openpyxl import load_workbook

from events.models import Event, Participant, Registration
from gallery.models import GalleryAlbum, GalleryImage
from management.constants import GROUP_LEADERSHIP, GROUP_MEDIA, GROUP_RECEPTION
from management.views import management_album_detail


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ManagementViewsBaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.future_date = timezone.localdate() + timedelta(days=10)

        self.leadership_group = Group.objects.create(name=GROUP_LEADERSHIP)
        self.reception_group = Group.objects.create(name=GROUP_RECEPTION)
        self.media_group = Group.objects.create(name=GROUP_MEDIA)

        self.leadership_user = User.objects.create_user(
            username="lider",
            password="pass123",
            email="lider@example.com",
        )
        self.leadership_user.groups.add(self.leadership_group)

        self.reception_user = User.objects.create_user(
            username="rececao",
            password="pass123",
            email="rececao@example.com",
        )
        self.reception_user.groups.add(self.reception_group)

        self.media_user = User.objects.create_user(
            username="media",
            password="pass123",
            email="media@example.com",
        )
        self.media_user.groups.add(self.media_group)

        self.no_group_user = User.objects.create_user(
            username="sem_grupo",
            password="pass123",
            email="semgrupo@example.com",
        )

    def create_event(self, **kwargs):
        data = {
            "title": "Evento Teste",
            "date": self.future_date,
            "location": "Lisboa",
            "price": Decimal("10.00"),
            "is_active": True,
            "is_archived": False,
            "registration_deadline": timezone.now() + timedelta(days=2),
        }
        data.update(kwargs)
        return Event.objects.create(**data)

    def create_registration(self, event, **kwargs):
        data = {
            "event": event,
            "buyer_name": "Comprador Teste",
            "buyer_email": "comprador@example.com",
            "phone": "912345678",
            "ticket_qty": 1,
            "payment_method": "LOCAL",
        }
        data.update(kwargs)
        return Registration.objects.create(**data)

    def create_participant(self, registration, **kwargs):
        data = {
            "registration": registration,
            "full_name": "Participante Teste",
            "ticket_code": f"TKT-{registration.id}-{Participant.objects.count() + 1}",
            "is_paid": False,
            "checked_in": False,
        }
        data.update(kwargs)
        return Participant.objects.create(**data)

    def create_album(self, **kwargs):
        data = {
            "title": f"Album {GalleryAlbum.objects.count() + 1}",
            "album_date": timezone.localdate(),
            "expires_at": timezone.now() + timedelta(days=5),
            "is_active": True,
            "created_by": self.media_user,
        }
        data.update(kwargs)
        return GalleryAlbum.objects.create(**data)


class ManagementHubAndGalleryViewsTest(ManagementViewsBaseTest):
    def test_dashboard_reception_acede(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.get(reverse("management:home"))

        self.assertEqual(response.status_code, 200)

    def test_events_hub_reception_acede(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.get(reverse("management:events_hub"))

        self.assertEqual(response.status_code, 200)

    def test_gallery_hub_media_acede(self):
        self.client.login(username="media", password="pass123")

        response = self.client.get(reverse("management:gallery_hub"))

        self.assertEqual(response.status_code, 200)

    def test_gallery_hub_sem_grupo_bloqueado(self):
        self.client.login(username="sem_grupo", password="pass123")

        response = self.client.get(reverse("management:gallery_hub"))

        self.assertEqual(response.status_code, 403)

    def test_gallery_albums_list_filtra_ativos_e_nao_expirados(self):
        self.client.login(username="media", password="pass123")
        visible = self.create_album(title="Album Visivel")
        self.create_album(title="Album Inativo", is_active=False)
        self.create_album(
            title="Album Expirado",
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(reverse("management:gallery_albums_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.title)
        self.assertNotContains(response, "Album Inativo")
        self.assertNotContains(response, "Album Expirado")
        self.assertEqual(
            response.context["detail_url_name"],
            "management:management_album_detail",
        )

    def test_management_album_detail_redireciona_quando_album_expirou(self):
        self.client.login(username="media", password="pass123")
        album = self.create_album(
            title="Album Expirado",
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(
            reverse("management:management_album_detail", kwargs={"slug": album.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("management:gallery_albums_list"))

    def test_management_album_detail_get_filtra_imagens_expiradas(self):
        self.client.login(username="media", password="pass123")
        album = self.create_album(title="Album Gestao")
        keep = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/keep.jpg",
            uploaded_by=self.media_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/drop.jpg",
            uploaded_by=self.media_user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(
            reverse("management:management_album_detail", kwargs={"slug": album.slug})
        )

        self.assertEqual(response.status_code, 200)
        images = list(response.context["images"])
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].id, keep.id)

    @patch("management.views.GalleryImage.objects.create")
    def test_management_album_detail_post_adiciona_imagens(self, mock_create):
        self.client.login(username="media", password="pass123")
        album = self.create_album(title="Album Upload")
        file1 = SimpleUploadedFile("foto1.jpg", b"fake-image-1", content_type="image/jpeg")
        file2 = SimpleUploadedFile("foto2.jpg", b"fake-image-2", content_type="image/jpeg")

        response = self.client.post(
            reverse("management:management_album_detail", kwargs={"slug": album.slug}),
            {"images": [file1, file2]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_create.call_count, 2)

    def test_management_album_detail_post_sem_ficheiros_mostra_erro(self):
        album = self.create_album(title="Album Sem Upload")
        request = self.factory.post(
            reverse("management:management_album_detail", kwargs={"slug": album.slug})
        )
        request.user = self.media_user
        request.session = self.client.session
        request._files = MultiValueDict({"images": []})

        from django.contrib.messages.storage.fallback import FallbackStorage

        setattr(request, "_messages", FallbackStorage(request))

        response = management_album_detail(request, slug=album.slug)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("management:management_album_detail", kwargs={"slug": album.slug}),
        )
        messages = [message.message for message in get_messages(request)]
        self.assertTrue(any("Seleciona pelo menos uma imagem" in message for message in messages))


class ManagementRegistrationsAjaxAndReportsTest(ManagementViewsBaseTest):
    def setUp(self):
        super().setUp()
        self.event = self.create_event(title="Evento Gestao")

    def test_event_registrations_aplica_filtros_e_kpis(self):
        self.client.login(username="rececao", password="pass123")
        reg_paid = self.create_registration(
            self.event,
            buyer_name="Ana Silva",
            buyer_email="ana@example.com",
            ticket_qty=1,
        )
        self.create_participant(
            reg_paid,
            full_name="Ana Silva",
            ticket_code="CODE-ANA",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=True,
            checked_in_at=timezone.now(),
        )
        reg_unpaid = self.create_registration(
            self.event,
            buyer_name="Bruno Costa",
            buyer_email="bruno@example.com",
            ticket_qty=1,
        )
        self.create_participant(
            reg_unpaid,
            full_name="Bruno Costa",
            ticket_code="CODE-BRUNO",
            is_paid=False,
            checked_in=False,
        )

        response = self.client.get(
            reverse("management:event_regs", kwargs={"event_id": self.event.id}),
            {"q": "Ana", "paid": "1", "checkin": "1"},
        )

        self.assertEqual(response.status_code, 200)
        page_items = list(response.context["page_obj"].object_list)
        self.assertEqual(len(page_items), 1)
        self.assertEqual(page_items[0].id, reg_paid.id)
        self.assertEqual(response.context["filters"]["q"], "Ana")
        self.assertEqual(response.context["kpis"]["total_regs"], 2)
        self.assertEqual(response.context["kpis"]["total_participants"], 2)
        self.assertEqual(response.context["kpis"]["total_paid_participants"], 1)
        self.assertEqual(response.context["kpis"]["total_checkins"], 1)

    def test_event_registrations_filtra_pendentes_de_pagamento_e_checkin(self):
        self.client.login(username="rececao", password="pass123")
        reg_ok = self.create_registration(self.event, buyer_name="Pago")
        self.create_participant(
            reg_ok,
            ticket_code="REG-OK",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=True,
            checked_in_at=timezone.now(),
        )
        reg_pending = self.create_registration(self.event, buyer_name="Pendente")
        self.create_participant(
            reg_pending,
            ticket_code="REG-PENDING",
            is_paid=False,
            checked_in=False,
        )

        response = self.client.get(
            reverse("management:event_regs", kwargs={"event_id": self.event.id}),
            {"paid": "0", "checkin": "0"},
        )

        self.assertEqual(response.status_code, 200)
        page_items = list(response.context["page_obj"].object_list)
        self.assertEqual(len(page_items), 1)
        self.assertEqual(page_items[0].id, reg_pending.id)

    def test_create_event_post_invalido_retorna_formulario(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.post(reverse("management:create_event"), {"title": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verifica os campos do formulário")

    def test_edit_event_post_invalido_retorna_formulario(self):
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(title="Evento Editar")

        response = self.client.post(
            reverse("management:event_edit", kwargs={"event_id": event.id}),
            {"title": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verifica os campos do formulário")

    def test_mark_registration_paid_full_ajax_retorna_json(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event, ticket_qty=2)
        self.create_participant(registration, ticket_code="PAID-1")
        self.create_participant(registration, ticket_code="PAID-2")

        response = self.client.post(
            reverse("management:mark_registration_paid_full", kwargs={"reg_id": registration.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["message"], "Pagamento total confirmado")
        registration.refresh_from_db()
        self.assertTrue(registration.is_paid)

    def test_toggle_participant_paid_ajax_retorna_estado_atualizado(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(registration, ticket_code="TOGGLE-PAID")

        response = self.client.post(
            reverse("management:toggle_participant_paid", kwargs={"participant_id": participant.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["participant"]["is_paid"])
        self.assertEqual(payload["registration"]["paid_amount"], "10.00")

    def test_toggle_participant_checkin_ajax_bloqueia_nao_pago(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(registration, ticket_code="BLOCK-CHECKIN")

        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("pagamento confirmado", payload["error"])

    def test_toggle_participant_checkin_ajax_confirma_quando_pago(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(
            registration,
            ticket_code="OK-CHECKIN",
            is_paid=True,
            paid_at=timezone.now(),
        )

        response = self.client.post(
            reverse("management:toggle_participant_checkin", kwargs={"participant_id": participant.id}),
            {"value": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["participant"]["checked_in"])

    def test_checkin_all_ajax_bloqueia_pagamento_pendente(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event, ticket_qty=2)
        self.create_participant(registration, ticket_code="CIN-1", is_paid=True, paid_at=timezone.now())
        self.create_participant(registration, ticket_code="CIN-2", is_paid=False)

        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": registration.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("por pagar", payload["error"])

    def test_checkin_all_ajax_confirma_todos(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event, ticket_qty=2)
        self.create_participant(registration, ticket_code="ALL-1", is_paid=True, paid_at=timezone.now())
        self.create_participant(registration, ticket_code="ALL-2", is_paid=True, paid_at=timezone.now())

        response = self.client.post(
            reverse("management:checkin_all", kwargs={"reg_id": registration.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["message"], "Check-in de todos os participantes registado")

    def test_scan_page_reception_acede(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.get(reverse("management:scan"))

        self.assertEqual(response.status_code, 200)

    def test_scan_checkin_api_sem_codigo_retorna_400(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.post(reverse("management:scan_checkin_api"), {"ticket_code": ""})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "invalid")

    def test_scan_checkin_api_bilhete_nao_encontrado(self):
        self.client.login(username="rececao", password="pass123")

        response = self.client.post(
            reverse("management:scan_checkin_api"),
            {"ticket_code": "NAO-EXISTE"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "not_found")

    def test_scan_checkin_api_pagamento_pendente(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(
            registration,
            ticket_code="PENDING-1",
            is_paid=False,
        )

        response = self.client.post(
            reverse("management:scan_checkin_api"),
            {"ticket_code": participant.ticket_code},
        )

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertEqual(payload["status"], "payment_pending")
        self.assertEqual(payload["lookup_url"], f"/gestao/inscricao/{registration.id}/grupo/")

    def test_scan_checkin_api_participante_ja_fez_checkin(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(
            registration,
            ticket_code="DONE-1",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=True,
            checked_in_at=timezone.now(),
        )

        response = self.client.post(
            reverse("management:scan_checkin_api"),
            {"ticket_code": participant.ticket_code},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["status"], "already_checked_in")

    def test_scan_checkin_api_confirma_checkin(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(
            registration,
            ticket_code="OK-1",
            is_paid=True,
            paid_at=timezone.now(),
        )

        response = self.client.post(
            reverse("management:scan_checkin_api"),
            {"ticket_code": participant.ticket_code},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "checked_in")
        participant.refresh_from_db()
        self.assertTrue(participant.checked_in)

    def test_ticket_lookup_mostra_participante(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(registration, ticket_code="LOOKUP-1")

        response = self.client.get(
            reverse("management:ticket_lookup", kwargs={"ticket_code": participant.ticket_code})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["participant"].id, participant.id)

    def test_registration_group_mostra_contagens_e_kpis(self):
        self.client.login(username="rececao", password="pass123")
        registration = self.create_registration(self.event, ticket_qty=2)
        self.create_participant(
            registration,
            ticket_code="GROUP-1",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=True,
            checked_in_at=timezone.now(),
        )
        self.create_participant(registration, ticket_code="GROUP-2", is_paid=False, checked_in=False)

        response = self.client.get(
            reverse("management:registration_group", kwargs={"reg_id": registration.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_participants"], 2)
        self.assertEqual(response.context["paid_participants"], 1)
        self.assertEqual(response.context["checked_participants"], 1)
        self.assertEqual(response.context["kpis"]["total_regs"], 1)

    def test_export_event_registrations_excel_gera_ficheiro(self):
        self.client.login(username="lider", password="pass123")
        registration = self.create_registration(self.event)
        participant = self.create_participant(
            registration,
            ticket_code="XLS-1",
            is_paid=True,
            paid_at=timezone.now(),
        )

        response = self.client.get(
            reverse(
                "management:export_event_registrations_excel",
                kwargs={"event_id": self.event.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(f'inscricoes-{self.event.slug}.xlsx', response["Content-Disposition"])

        workbook = load_workbook(filename=BytesIO(response.content))
        worksheet = workbook.active
        self.assertEqual(worksheet.title, "Inscrições")
        self.assertEqual(worksheet["A2"].value, self.event.title)
        self.assertEqual(worksheet["E2"].value, participant.full_name)
        self.assertEqual(worksheet["F2"].value, participant.ticket_code)

    def test_reports_lista_eventos_para_lideranca(self):
        self.client.login(username="lider", password="pass123")
        self.create_event(title="Evento Relatorio 2")

        response = self.client.get(reverse("management:reports"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["events"].count(), 2)

    def test_event_report_calcula_metricas(self):
        self.client.login(username="lider", password="pass123")
        registration = self.create_registration(self.event, ticket_qty=2)
        self.create_participant(
            registration,
            ticket_code="REPORT-1",
            is_paid=True,
            paid_at=timezone.now(),
            checked_in=True,
            checked_in_at=timezone.now(),
        )
        self.create_participant(
            registration,
            ticket_code="REPORT-2",
            is_paid=False,
            checked_in=False,
        )

        response = self.client.get(
            reverse("management:event_report", kwargs={"event_id": self.event.id})
        )

        self.assertEqual(response.status_code, 200)
        report = response.context["report"]
        self.assertEqual(report["total_regs"], 1)
        self.assertEqual(report["total_participants"], 2)
        self.assertEqual(report["total_paid"], 1)
        self.assertEqual(report["total_checkins"], 1)
        self.assertEqual(report["expected_amount"], Decimal("20.00"))
        self.assertEqual(report["received_amount"], Decimal("10.00"))
        self.assertEqual(report["pending_amount"], Decimal("10.00"))
        self.assertEqual(report["checkin_rate"], 50)
        self.assertEqual(report["paid_rate"], 50)