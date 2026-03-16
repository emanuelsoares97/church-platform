from django.contrib import admin

from .forms import GalleryAlbumForm
from .models import GalleryAlbum, GalleryImage


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 0
    fields = ("image", "uploaded_by", "uploaded_at", "expires_at")
    readonly_fields = ("uploaded_at", "expires_at")


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    """
    Administração dos álbuns da galeria.
    """
    form = GalleryAlbumForm

    list_display = (
        "title",
        "album_date",
        "retention_days",
        "expires_at",
        "is_active",
        "created_by",
        "image_count",
    )
    list_filter = ("is_active", "retention_days", "album_date", "created_at")
    search_fields = ("title", "description", "slug")
    readonly_fields = ("created_at", "expires_at", "slug")
    inlines = [GalleryImageInline]


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """
    Administração das imagens da galeria.
    """
    list_display = (
        "album",
        "uploaded_by",
        "uploaded_at",
        "expires_at",
    )
    list_filter = ("uploaded_at", "expires_at")
    search_fields = ("album__title",)
    readonly_fields = ("uploaded_at", "expires_at")