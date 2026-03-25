from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from events.models import Event
from management.constants import GROUP_LEADERSHIP, GROUP_RECEPTION


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class EventManagementPermissionsTest(TestCase):
    """Testa permissões de acesso às views de gestão de eventos."""

    def setUp(self):
        """Cria utilizadores, grupos e cliente."""
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

    def create_event(self, **kwargs):
        """Helper para criar eventos com defaults."""
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

    def test_events_list_anon_bloqueado(self):
        """Utilizador anónimo não acede à lista de eventos."""
        response = self.client.get(reverse("management:events_list"))
        self.assertEqual(response.status_code, 302)

    def test_events_list_reception_acede(self):
        """Receção acede à lista de eventos."""
        self.client.login(username="rececao", password="pass123")
        create_event = self.create_event(title="Evento 1")
        response = self.client.get(reverse("management:events_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, create_event.title)

    def test_events_list_leadership_acede(self):
        """Liderança acede à lista de eventos."""
        self.client.login(username="lider", password="pass123")
        create_event = self.create_event(title="Evento 1")
        response = self.client.get(reverse("management:events_list"))
        self.assertEqual(response.status_code, 200)

    def test_events_list_sem_grupo_bloqueado(self):
        """Utilizador sem grupo não acede à lista."""
        self.client.login(username="sem_grupo", password="pass123")
        response = self.client.get(reverse("management:events_list"))
        self.assertEqual(response.status_code, 403)

    def test_events_admin_list_anon_bloqueado(self):
        """Utilizador anónimo não acede à lista administrativa."""
        response = self.client.get(reverse("management:events_admin_list"))
        self.assertEqual(response.status_code, 302)

    def test_events_admin_list_leadership_acede(self):
        """Apenas liderança acede à lista administrativa."""
        self.client.login(username="lider", password="pass123")
        response = self.client.get(reverse("management:events_admin_list"))
        self.assertEqual(response.status_code, 200)

    def test_events_admin_list_reception_bloqueado(self):
        """Receção não acede à lista administrativa."""
        self.client.login(username="rececao", password="pass123")
        response = self.client.get(reverse("management:events_admin_list"))
        self.assertEqual(response.status_code, 403)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class EventManagementActionsTest(TestCase):
    """Testa ações de gestão: criar, editar, ativar, desativar, arquivar."""

    def setUp(self):
        """Cria utilizadores, grupos e cliente."""
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

        self.client = Client()
        self.future_date = timezone.localdate() + timedelta(days=10)

    def create_event(self, **kwargs):
        """Helper para criar eventos."""
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

    def test_create_event_get_funciona(self):
        """GET na página de criar evento funciona."""
        self.client.login(username="rececao", password="pass123")
        response = self.client.get(reverse("management:create_event"))
        self.assertEqual(response.status_code, 200)

    def test_create_event_post_valido_cria(self):
        """POST com dados válidos cria o evento."""
        self.client.login(username="rececao", password="pass123")
        payload = {
            "title": "Novo Evento",
            "date": self.future_date,
            "location": "Lisboa",
            "price": "10.00",
            "registration_deadline": timezone.now() + timedelta(days=2),
        }
        response = self.client.post(reverse("management:create_event"), payload)

        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(title="Novo Evento")
        self.assertTrue(event.is_active)
        self.assertFalse(event.is_archived)

    def test_create_event_leadership_acede(self):
        """Liderança pode criar eventos."""
        self.client.login(username="lider", password="pass123")
        payload = {
            "title": "Novo Evento Lider",
            "date": self.future_date,
            "location": "Lisboa",
            "price": "5.00",
            "registration_deadline": timezone.now() + timedelta(days=1),
        }
        response = self.client.post(reverse("management:create_event"), payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(title="Novo Evento Lider").exists())

    def test_edit_event_get_mostra_formulario(self):
        """GET em edição mostra o formulário com dados do evento."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(title="Original")

        response = self.client.get(
            reverse("management:event_edit", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)

    def test_edit_event_post_atualiza(self):
        """POST em edição atualiza o evento."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(title="Original")

        payload = {
            "title": "Título Modificado",
            "date": self.future_date,
            "location": "Porto",
            "price": "20.00",
            "registration_deadline": timezone.now() + timedelta(days=3),
        }
        response = self.client.post(
            reverse("management:event_edit", kwargs={"event_id": event.id}), payload
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.title, "Título Modificado")
        self.assertEqual(event.location, "Porto")

    def test_edit_event_com_next_redireciona_corretamente(self):
        """Quando há 'next', o redirect vai para lá."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event()
        next_url = reverse("management:events_list")

        payload = {
            "title": "Título Novo",
            "date": self.future_date,
            "location": "Lisboa",
            "price": "10.00",
            "registration_deadline": timezone.now() + timedelta(days=2),
            "next": next_url,
        }
        response = self.client.post(
            reverse("management:event_edit", kwargs={"event_id": event.id}),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_activate_event_post_requerido(self):
        """GET em activate_event não funciona."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(is_active=False)

        response = self.client.get(
            reverse("management:event_activate", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 405)

    def test_activate_event_post_funciona(self):
        """POST ativa o evento."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(is_active=False)

        response = self.client.post(
            reverse("management:event_activate", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertTrue(event.is_active)

    def test_deactivate_event_post_funciona(self):
        """POST desativa o evento."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(is_active=True)

        response = self.client.post(
            reverse("management:event_deactivate", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertFalse(event.is_active)

    def test_activate_event_reception_acede(self):
        """Receção pode ativar eventos."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(is_active=False)

        response = self.client.post(
            reverse("management:event_activate", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)

    def test_archive_event_anon_bloqueado(self):
        """Utilizador anónimo não pode arquivar."""
        event = self.create_event()
        response = self.client.post(
            reverse("management:event_archive", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)

    def test_archive_event_reception_bloqueado(self):
        """Receção não pode arquivar (apenas liderança)."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event()

        response = self.client.post(
            reverse("management:event_archive", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_archive_event_leadership_funciona(self):
        """Liderança pode arquivar e o evento fica arquivado."""
        self.client.login(username="lider", password="pass123")
        event = self.create_event(is_archived=False)

        response = self.client.post(
            reverse("management:event_archive", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertTrue(event.is_archived)

    def test_unarchive_event_leadership_funciona(self):
        """Liderança pode desarquivar o evento."""
        self.client.login(username="lider", password="pass123")
        event = self.create_event(is_archived=True)

        response = self.client.post(
            reverse("management:event_unarchive", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertFalse(event.is_archived)

    def test_active_desactive_mantem_evento_nao_arquivado(self):
        """Ativar/desativar não mexe no estado de arquivo."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(is_active=True, is_archived=False)

        self.client.post(
            reverse("management:event_deactivate", kwargs={"event_id": event.id})
        )
        event.refresh_from_db()
        self.assertFalse(event.is_active)
        self.assertFalse(event.is_archived)

    def test_event_passado_continua_na_gestao_se_nao_arquivado(self):
        """Evento no passado aparece na lista se não estiver arquivado."""
        self.client.login(username="rececao", password="pass123")
        past_date = timezone.localdate() - timedelta(days=5)
        event = self.create_event(date=past_date, is_archived=False)

        response = self.client.get(reverse("management:events_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event.title)

    def test_event_futuro_com_inscricoes_encerradas_continua_editavel(self):
        """Evento futuro com prazo fechado ainda pode ser editado."""
        self.client.login(username="rececao", password="pass123")
        event = self.create_event(
            registration_deadline=timezone.now() - timedelta(minutes=1)
        )

        response = self.client.get(
            reverse("management:event_edit", kwargs={"event_id": event.id})
        )

        self.assertEqual(response.status_code, 200)
