from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from gallery.models import GalleryAlbum, GalleryImage
from management.constants import GROUP_MEDIA


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class GalleryViewsTest(TestCase):
    def setUp(self):
        self.media_group = Group.objects.create(name=GROUP_MEDIA)
        self.media_user = User.objects.create_user(
            username="media",
            password="pass123",
            email="media@example.com",
        )
        self.media_user.groups.add(self.media_group)
        self.common_user = User.objects.create_user(
            username="common",
            password="pass123",
            email="common@example.com",
        )

    def test_album_list_mostra_apenas_ativos_e_nao_expirados(self):
        visible = GalleryAlbum.objects.create(
            title="Visivel",
            is_active=True,
            expires_at=timezone.now() + timedelta(days=1),
        )
        GalleryAlbum.objects.create(
            title="Inativo",
            is_active=False,
            expires_at=timezone.now() + timedelta(days=1),
        )
        GalleryAlbum.objects.create(
            title="Expirado",
            is_active=True,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(reverse("gallery:album_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.title)
        self.assertNotContains(response, "Inativo")
        self.assertNotContains(response, "Expirado")
        self.assertEqual(response.context["detail_url_name"], "gallery:album_detail")

    def test_album_list_mostra_album_sempre_disponivel(self):
        always = GalleryAlbum.objects.create(
            title="Sempre Disponivel",
            is_active=True,
            retention_days=GalleryAlbum.RETENTION_ALWAYS,
            expires_at=None,
        )

        response = self.client.get(reverse("gallery:album_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, always.title)

    def test_album_detail_404_para_album_inativo(self):
        album = GalleryAlbum.objects.create(
            title="Album Inativo",
            is_active=False,
            expires_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(reverse("gallery:album_detail", kwargs={"slug": album.slug}))

        self.assertEqual(response.status_code, 404)

    def test_album_detail_redireciona_quando_album_expirado(self):
        album = GalleryAlbum.objects.create(
            title="Album Expirado",
            is_active=True,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(reverse("gallery:album_detail", kwargs={"slug": album.slug}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:album_list"))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("já não está disponível" in message for message in messages))

    def test_album_detail_filtra_imagens_expiradas(self):
        album = GalleryAlbum.objects.create(
            title="Album Ativo",
            is_active=True,
            expires_at=timezone.now() + timedelta(days=1),
            created_by=self.media_user,
        )
        keep = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/keep.jpg",
            uploaded_by=self.media_user,
            expires_at=timezone.now() + timedelta(hours=2),
        )
        GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/drop.jpg",
            uploaded_by=self.media_user,
            expires_at=timezone.now() - timedelta(minutes=2),
        )

        response = self.client.get(reverse("gallery:album_detail", kwargs={"slug": album.slug}))

        self.assertEqual(response.status_code, 200)
        images = list(response.context["images"])
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].id, keep.id)

    def test_create_album_redireciona_para_login_quando_anonimo(self):
        response = self.client.get(reverse("gallery:create_album"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_create_album_retorna_403_para_utilizador_sem_grupo(self):
        self.client.login(username="common", password="pass123")

        response = self.client.get(reverse("gallery:create_album"))

        self.assertEqual(response.status_code, 403)

    def test_create_album_get_para_media_carrega_formulario(self):
        self.client.login(username="media", password="pass123")

        response = self.client.get(reverse("gallery:create_album"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_create_album_post_valido_cria_album_e_redireciona(self):
        self.client.login(username="media", password="pass123")
        payload = {
            "title": "Novo Album",
            "description": "Descricao",
            "retention_days": 30,
            "is_active": True,
        }

        response = self.client.post(reverse("gallery:create_album"), payload)

        self.assertEqual(response.status_code, 302)
        album = GalleryAlbum.objects.get(title="Novo Album")
        self.assertEqual(album.created_by, self.media_user)
        self.assertTrue(album.is_active)
        self.assertEqual(response.url, reverse("gallery:album_detail", kwargs={"slug": album.slug}))

    def test_create_album_post_invalido_retorna_mesma_pagina(self):
        self.client.login(username="media", password="pass123")

        response = self.client.post(reverse("gallery:create_album"), {"title": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verifica os campos do formulário")

    def test_delete_image_get_rejeita_pedido(self):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album", created_by=self.media_user)
        image = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/image.jpg",
            uploaded_by=self.media_user,
        )

        response = self.client.get(reverse("gallery:delete_image", kwargs={"image_id": image.id}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:album_detail", kwargs={"slug": album.slug}))

    @patch("gallery.views.get_object_or_404")
    @patch("gallery.views.destroy")
    def test_delete_image_post_remove_cloudinary_e_registo(self, mock_destroy, mock_get_object):
        self.client.login(username="media", password="pass123")
        fake_image = SimpleNamespace(
            id=99,
            album=SimpleNamespace(slug="album-x"),
            image=SimpleNamespace(public_id="church-platform/gallery/image_1"),
            delete=MagicMock(),
        )
        mock_get_object.return_value = fake_image

        response = self.client.post(reverse("gallery:delete_image", kwargs={"image_id": 99}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:album_detail", kwargs={"slug": "album-x"}))
        mock_destroy.assert_called_once_with(
            "church-platform/gallery/image_1",
            invalidate=True,
            resource_type="image",
        )
        fake_image.delete.assert_called_once()

    @patch("gallery.views.get_object_or_404")
    @patch("gallery.views.destroy")
    def test_delete_image_post_com_erro_mostra_mensagem(self, mock_destroy, mock_get_object):
        self.client.login(username="media", password="pass123")
        fake_image = SimpleNamespace(
            id=45,
            album=SimpleNamespace(slug="album-y"),
            image=SimpleNamespace(public_id="church-platform/gallery/image_2"),
            delete=MagicMock(),
        )
        mock_get_object.return_value = fake_image
        mock_destroy.side_effect = Exception("cloud error")

        response = self.client.post(reverse("gallery:delete_image", kwargs={"image_id": 45}))

        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Não foi possível eliminar a foto" in message for message in messages))
        fake_image.delete.assert_not_called()

    def test_delete_selected_images_rejeita_metodo_invalido(self):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album Method", created_by=self.media_user)

        response = self.client.get(reverse("gallery:delete_selected_images", kwargs={"slug": album.slug}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("gallery:album_detail", kwargs={"slug": album.slug}))

    def test_delete_selected_images_sem_ids_mostra_erro(self):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album No IDs", created_by=self.media_user)

        response = self.client.post(
            reverse("gallery:delete_selected_images", kwargs={"slug": album.slug}),
            {},
        )

        self.assertEqual(response.status_code, 302)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Nenhuma foto foi selecionada" in message for message in messages))

    @patch("gallery.views.destroy")
    def test_delete_selected_images_remove_varias_com_sucesso(self, mock_destroy):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album Multi", created_by=self.media_user)
        image1 = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/1.jpg",
            uploaded_by=self.media_user,
        )
        image2 = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/2.jpg",
            uploaded_by=self.media_user,
        )

        response = self.client.post(
            reverse("gallery:delete_selected_images", kwargs={"slug": album.slug}),
            {"selected_images": [str(image1.id), str(image2.id)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(GalleryImage.objects.filter(id=image1.id).exists())
        self.assertFalse(GalleryImage.objects.filter(id=image2.id).exists())
        self.assertEqual(mock_destroy.call_count, 2)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("2 fotos eliminadas com sucesso" in message for message in messages))

    @patch("gallery.views.destroy")
    def test_delete_selected_images_remove_uma_com_sucesso(self, mock_destroy):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album Single", created_by=self.media_user)
        image = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/single.jpg",
            uploaded_by=self.media_user,
        )

        response = self.client.post(
            reverse("gallery:delete_selected_images", kwargs={"slug": album.slug}),
            {"selected_images": [str(image.id)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(GalleryImage.objects.filter(id=image.id).exists())
        mock_destroy.assert_called_once()
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("1 foto eliminada com sucesso" in message for message in messages))

    @patch("gallery.views.destroy")
    def test_delete_selected_images_todas_falham_mostra_erro(self, mock_destroy):
        self.client.login(username="media", password="pass123")
        album = GalleryAlbum.objects.create(title="Album Fail", created_by=self.media_user)
        image = GalleryImage.objects.create(
            album=album,
            image="church-platform/gallery/fail.jpg",
            uploaded_by=self.media_user,
        )
        mock_destroy.side_effect = Exception("boom")

        response = self.client.post(
            reverse("gallery:delete_selected_images", kwargs={"slug": album.slug}),
            {"selected_images": [str(image.id)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(GalleryImage.objects.filter(id=image.id).exists())
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("Não foi possível eliminar as fotos selecionadas" in message for message in messages))
