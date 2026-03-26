from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from gallery.models import GalleryAlbum, GalleryImage


class GalleryAlbumModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="media_user",
            email="media@example.com",
            password="pass123",
        )

    def test_save_gera_slug_automatico(self):
        album = GalleryAlbum.objects.create(title="Culto Domingo", created_by=self.user)

        self.assertEqual(album.slug, "culto-domingo")

    def test_save_gera_slug_unico_quando_ja_existe(self):
        GalleryAlbum.objects.create(title="Culto Domingo", created_by=self.user)
        album = GalleryAlbum.objects.create(title="Culto Domingo", created_by=self.user)

        self.assertEqual(album.slug, "culto-domingo-2")

    def test_save_define_expires_at_com_base_no_retention_days(self):
        before = timezone.now()
        album = GalleryAlbum.objects.create(
            title="Culto Jovens",
            retention_days=15,
            created_by=self.user,
        )
        after = timezone.now()

        self.assertIsNotNone(album.expires_at)
        self.assertGreaterEqual(album.expires_at, before + timedelta(days=15))
        self.assertLessEqual(album.expires_at, after + timedelta(days=15, seconds=1))

    def test_save_nao_substitui_expires_at_quando_ja_definido(self):
        custom_expire = timezone.now() + timedelta(days=90)
        album = GalleryAlbum.objects.create(
            title="Evento Especial",
            retention_days=7,
            expires_at=custom_expire,
            created_by=self.user,
        )

        self.assertEqual(album.expires_at, custom_expire)

    def test_is_expired_true_quando_passou_data(self):
        album = GalleryAlbum.objects.create(
            title="Album Expirado",
            expires_at=timezone.now() - timedelta(minutes=1),
            created_by=self.user,
        )

        self.assertTrue(album.is_expired())

    def test_is_expired_false_quando_ainda_valido(self):
        album = GalleryAlbum.objects.create(
            title="Album Ativo",
            expires_at=timezone.now() + timedelta(days=1),
            created_by=self.user,
        )

        self.assertFalse(album.is_expired())

    def test_is_expired_false_quando_sempre_disponivel(self):
        album = GalleryAlbum.objects.create(
            title="Album Sempre",
            retention_days=GalleryAlbum.RETENTION_ALWAYS,
            created_by=self.user,
        )

        self.assertIsNone(album.expires_at)
        self.assertFalse(album.is_expired())

    def test_is_publicly_available_respeita_estado_e_expiracao(self):
        album = GalleryAlbum.objects.create(
            title="Album Publico",
            is_active=True,
            expires_at=timezone.now() + timedelta(hours=1),
            created_by=self.user,
        )
        self.assertTrue(album.is_publicly_available())

        album.is_active = False
        self.assertFalse(album.is_publicly_available())

    def test_image_count_retorna_total_de_imagens(self):
        album = GalleryAlbum.objects.create(title="Album com Fotos", created_by=self.user)
        GalleryImage.objects.create(album=album, image="church-platform/gallery/f1.jpg", uploaded_by=self.user)
        GalleryImage.objects.create(album=album, image="church-platform/gallery/f2.jpg", uploaded_by=self.user)

        self.assertEqual(album.image_count(), 2)

    def test_str_retorna_titulo(self):
        album = GalleryAlbum.objects.create(title="Retiro", created_by=self.user)

        self.assertEqual(str(album), "Retiro")


class GalleryImageModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="media_user_2",
            email="media2@example.com",
            password="pass123",
        )
        self.album = GalleryAlbum.objects.create(
            title="Album Base",
            expires_at=timezone.now() + timedelta(days=30),
            created_by=self.user,
        )

    def test_save_herda_expires_at_do_album(self):
        image = GalleryImage.objects.create(
            album=self.album,
            image="church-platform/gallery/herda.jpg",
            uploaded_by=self.user,
        )

        self.assertEqual(image.expires_at, self.album.expires_at)

    def test_save_respeita_expires_at_proprio(self):
        custom_expire = timezone.now() + timedelta(days=1)
        image = GalleryImage.objects.create(
            album=self.album,
            image="church-platform/gallery/custom.jpg",
            uploaded_by=self.user,
            expires_at=custom_expire,
        )

        self.assertEqual(image.expires_at, custom_expire)

    def test_is_expired_true_quando_imagem_expirou(self):
        image = GalleryImage.objects.create(
            album=self.album,
            image="church-platform/gallery/old.jpg",
            uploaded_by=self.user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        self.assertTrue(image.is_expired())

    def test_is_expired_false_quando_imagem_ainda_valida(self):
        image = GalleryImage.objects.create(
            album=self.album,
            image="church-platform/gallery/new.jpg",
            uploaded_by=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        self.assertFalse(image.is_expired())

    def test_str_formata_titulo_do_album_e_pk(self):
        image = GalleryImage.objects.create(
            album=self.album,
            image="church-platform/gallery/str.jpg",
            uploaded_by=self.user,
        )

        self.assertIn("Album Base - imagem", str(image))
