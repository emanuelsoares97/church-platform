import logging

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from gallery.forms import GalleryAlbumForm
from gallery.models import GalleryAlbum, GalleryImage
from management.permissions import media_or_leadership_required


logger = logging.getLogger(__name__)


@media_or_leadership_required
def gallery_albums_list(request):
    """Lista de álbuns para gestão com filtro por estado."""
    state = request.GET.get("estado", "todos")

    albums = GalleryAlbum.objects.all().order_by("-album_date", "-created_at")

    if state == "ativos":
        albums = albums.filter(is_active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
    elif state == "desativados":
        albums = albums.filter(is_active=False)
    elif state == "expirados":
        albums = albums.filter(is_active=True, expires_at__isnull=False, expires_at__lte=timezone.now())

    return render(
        request,
        "management/gallery_albums_list.html",
        {
            "albums": albums,
            "state": state,
        },
    )


@media_or_leadership_required
def management_album_detail(request, slug):
    """Mostra o detalhe de um álbum em contexto de gestão e permite upload de fotos."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    images = album.images.order_by("-uploaded_at")

    if request.method == "POST" and "images" in request.FILES:
        uploaded_files = request.FILES.getlist("images")

        if not uploaded_files:
            messages.error(request, "Seleciona pelo menos uma imagem.")
            return redirect("management:management_album_detail", slug=album.slug)

        for file in uploaded_files:
            GalleryImage.objects.create(
                album=album,
                image=file,
                uploaded_by=request.user,
            )

        messages.success(request, "Fotos adicionadas com sucesso.")
        return redirect("management:management_album_detail", slug=album.slug)

    return render(
        request,
        "management/album_management_detail.html",
        {
            "album": album,
            "images": images,
        },
    )


@media_or_leadership_required
def edit_gallery_album(request, slug):
    """Edita os campos de um álbum da galeria (título, descrição, data, retenção)."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    if request.method == "POST":
        form = GalleryAlbumForm(request.POST, instance=album)

        if form.is_valid():
            form.save()
            messages.success(request, "Álbum atualizado com sucesso.")
            return redirect("management:management_album_detail", slug=album.slug)

        messages.error(request, "Verifica os campos do formulário.")
    else:
        form = GalleryAlbumForm(instance=album)

    return render(
        request,
        "management/edit_gallery_album.html",
        {
            "form": form,
            "album": album,
        },
    )


@media_or_leadership_required
@require_POST
def deactivate_gallery_album(request, slug):
    """Desativa um álbum, removendo-o da área pública."""
    album = get_object_or_404(GalleryAlbum, slug=slug)
    album.is_active = False
    album.save(update_fields=["is_active"])

    messages.success(request, "Álbum desativado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")


@media_or_leadership_required
@require_POST
def activate_gallery_album(request, slug):
    """Ativa um álbum, tornando-o visível na área pública."""
    album = get_object_or_404(GalleryAlbum, slug=slug)
    album.is_active = True
    album.save(update_fields=["is_active"])

    messages.success(request, "Álbum ativado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")


@media_or_leadership_required
@require_POST
def delete_gallery_album(request, slug):
    """Elimina definitivamente um álbum da gestão e da base de dados."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    for image in album.images.all():
        public_id = getattr(image.image, "public_id", None)
        if public_id:
            try:
                from management import views as management_views

                management_views.destroy(public_id, invalidate=True, resource_type="image")
            except Exception as error:
                # Mantemos a eliminação do álbum mesmo se um ficheiro remoto falhar.
                logger.warning(
                    "Falha ao eliminar imagem no Cloudinary durante eliminação do álbum",
                    extra={
                        "album_id": album.id,
                        "album_slug": album.slug,
                        "public_id": public_id,
                        "error": str(error),
                    },
                )

    album.delete()
    messages.success(request, "Álbum eliminado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")
