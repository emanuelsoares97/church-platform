from io import BytesIO
from unittest.mock import patch

from django import forms
from django.test import TestCase

from gallery.forms import GalleryAlbumForm, GalleryImageForm


class GalleryAlbumFormTest(TestCase):
    def test_form_valido_com_dados_minimos(self):
        form = GalleryAlbumForm(
            data={
                "title": "Culto de Domingo",
                "description": "Album semanal",
                "retention_days": 30,
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid())


class GalleryImageFormTest(TestCase):
    @patch("gallery.forms.optimize_uploaded_image")
    def test_clean_image_otimiza_upload_novo(self, mock_optimize):
        uploaded = BytesIO(b"fake-image-bytes")
        uploaded.name = "foto.jpg"
        sentinel = object()
        mock_optimize.return_value = sentinel

        form = GalleryImageForm()
        form.cleaned_data = {"image": uploaded}

        result = form.clean_image()

        self.assertIs(result, sentinel)
        mock_optimize.assert_called_once_with(uploaded)

    def test_clean_image_sem_imagem_retorna_none(self):
        form = GalleryImageForm()
        form.cleaned_data = {"image": None}

        result = form.clean_image()

        self.assertIsNone(result)

    @patch("gallery.forms.optimize_uploaded_image")
    def test_clean_image_lanca_validation_error_quando_falha_otimizacao(self, mock_optimize):
        uploaded = BytesIO(b"broken")
        uploaded.name = "broken.jpg"
        mock_optimize.side_effect = Exception("erro de processamento")

        form = GalleryImageForm()
        form.cleaned_data = {"image": uploaded}

        with self.assertRaises(forms.ValidationError):
            form.clean_image()
