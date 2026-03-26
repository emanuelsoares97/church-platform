from datetime import timedelta

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class GalleryAlbum(models.Model):
    """
    Álbum de galeria para celebrações, reuniões ou momentos da igreja.

    Cada álbum pode ter um prazo de expiração configurável.
    """

    RETENTION_ALWAYS = 0

    RETENTION_CHOICES = (
        (RETENTION_ALWAYS, "Sempre disponível"),
        (7, "7 dias"),
        (15, "15 dias"),
        (30, "30 dias"),
    )

    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    album_date = models.DateField(
        verbose_name="Data do culto / momento",
        null=True,
        blank=True,
    )

    retention_days = models.PositiveIntegerField(
        choices=RETENTION_CHOICES,
        default=30,
        verbose_name="Disponível durante",
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expira em",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_albums_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Álbum da galeria"
        verbose_name_plural = "Álbuns da galeria"

    def save(self, *args, **kwargs):
        """
        Gera slug automático e calcula a data de expiração.
        """
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2

            while GalleryAlbum.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        if self.retention_days == self.RETENTION_ALWAYS:
            # Álbuns sempre disponíveis não expiram automaticamente.
            self.expires_at = None
        elif not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.retention_days)

        super().save(*args, **kwargs)

    def is_expired(self):
        """
        Indica se o álbum já expirou.
        """
        return timezone.now() >= self.expires_at if self.expires_at else False

    def is_publicly_available(self):
        """
        Indica se o álbum deve aparecer na área pública.
        """
        return self.is_active and not self.is_expired()

    def lifecycle_state(self):
        """
        Retorna o estado funcional do álbum para gestão.
        """
        if not self.is_active:
            return "desativado"
        if self.is_expired():
            return "expirado"
        return "ativo"

    def image_count(self):
        """
        Retorna o número de imagens do álbum.
        """
        return self.images.count()

    def __str__(self):
        return self.title


class GalleryImage(models.Model):
    """
    Imagem pertencente a um álbum da galeria.
    """

    album = models.ForeignKey(
        GalleryAlbum,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = CloudinaryField(
        "gallery_image",
        folder="church-platform/gallery",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_images_uploaded",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expira em",
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Imagem da galeria"
        verbose_name_plural = "Imagens da galeria"

    def save(self, *args, **kwargs):
        """
        Herda a expiração do álbum caso ainda não tenha uma data definida.
        """
        if not self.expires_at and self.album_id:
            self.expires_at = self.album.expires_at

        super().save(*args, **kwargs)

    def is_expired(self):
        """
        Indica se a imagem já expirou.
        """
        return timezone.now() >= self.expires_at if self.expires_at else False

    def __str__(self):
        return f"{self.album.title} - imagem {self.pk}"