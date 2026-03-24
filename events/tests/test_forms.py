from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from events.forms import EventAdminForm, EventCreateForm


class EventCreateFormTest(TestCase):
    """Testa validações relevantes do formulário de eventos."""

    def get_valid_data(self):
        """Base de dados válidos para o formulário."""
        event_date = timezone.localdate() + timedelta(days=10)
        deadline = timezone.now() + timedelta(days=5)

        return {
            "title": "Evento de Teste",
            "description": "Descrição simples",
            "date": event_date.isoformat(),
            "location": "Lisboa",
            "price": "12.50",
            "registration_deadline": deadline.strftime("%Y-%m-%dT%H:%M"),
            "is_active": True,
            "ticket_qty": 10,
        }

    def test_form_valido_com_deadline_antes_da_data(self):
        """Aceita quando o prazo termina antes do dia do evento."""
        form = EventCreateForm(data=self.get_valid_data())

        self.assertTrue(form.is_valid())

    def test_form_invalido_com_deadline_depois_da_data(self):
        """Bloqueia quando o prazo fica depois da data do evento."""
        data = self.get_valid_data()
        future_event_date = timezone.localdate() + timedelta(days=2)
        data["date"] = future_event_date.isoformat()
        data["registration_deadline"] = (timezone.now() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")

        form = EventCreateForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("registration_deadline", form.errors)

    @patch("events.forms.optimize_uploaded_image")
    def test_clean_banner_image_otimiza_upload_novo(self, mock_optimize):
        """Quando há upload novo, chama a otimização."""
        uploaded = BytesIO(b"fake-image-bytes")
        uploaded.name = "banner.jpg"
        sentinel = object()
        mock_optimize.return_value = sentinel

        form = EventCreateForm()
        form.cleaned_data = {"banner_image": uploaded}

        result = form.clean_banner_image()

        self.assertIs(result, sentinel)
        mock_optimize.assert_called_once_with(uploaded)

    def test_clean_banner_image_ignora_objeto_existente_sem_read(self):
        """Quando vem recurso já guardado, devolve sem processar."""
        existing_resource = SimpleNamespace(public_id="event/banner_1")

        form = EventCreateForm()
        form.cleaned_data = {"banner_image": existing_resource}

        result = form.clean_banner_image()

        self.assertIs(result, existing_resource)


class EventAdminFormTest(TestCase):
    """Testa comportamento crítico do formulário de administração."""

    @patch("events.forms.optimize_uploaded_image")
    def test_clean_banner_image_otimiza_upload_novo(self, mock_optimize):
        """No admin, também otimiza apenas upload novo."""
        uploaded = BytesIO(b"fake-image-bytes")
        uploaded.name = "banner-admin.jpg"
        sentinel = object()
        mock_optimize.return_value = sentinel

        form = EventAdminForm()
        form.cleaned_data = {"banner_image": uploaded}

        result = form.clean_banner_image()

        self.assertIs(result, sentinel)
        mock_optimize.assert_called_once_with(uploaded)

    def test_clean_banner_image_ignora_recurso_existente(self):
        """No admin, não tenta abrir recurso já existente do Cloudinary."""
        existing_resource = SimpleNamespace(public_id="event/banner_2")

        form = EventAdminForm()
        form.cleaned_data = {"banner_image": existing_resource}

        result = form.clean_banner_image()

        self.assertIs(result, existing_resource)
