from cloudinary.uploader import destroy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import GalleryAlbum, GalleryImage


def album_list(request):
    """
    Lista apenas os álbuns ativos e não expirados.
    """
    now = timezone.now()

    albums = GalleryAlbum.objects.filter(
        is_active=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    ).order_by("-album_date", "-created_at")

    return render(
        request,
        "gallery/album_list.html",
        {"albums": albums},
    )


def album_detail(request, slug):
    """
    Mostra o detalhe de um álbum e permite upload de múltiplas imagens
    para utilizadores autenticados.
    """
    now = timezone.now()

    album = get_object_or_404(
        GalleryAlbum,
        slug=slug,
        is_active=True,
    )

    if album.is_expired():
        messages.error(request, "Este álbum já não está disponível.")
        return redirect("gallery:album_list")

    images = album.images.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    ).order_by("-uploaded_at")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Precisas de iniciar sessão para adicionar fotos.")
            return redirect("gallery:album_detail", slug=album.slug)

        uploaded_files = request.FILES.getlist("images")

        if not uploaded_files:
            messages.error(request, "Seleciona pelo menos uma imagem.")
            return redirect("gallery:album_detail", slug=album.slug)

        for file in uploaded_files:
            GalleryImage.objects.create(
                album=album,
                image=file,
                uploaded_by=request.user,
            )

        messages.success(request, "Fotos adicionadas com sucesso.")
        return redirect("gallery:album_detail", slug=album.slug)

    return render(
        request,
        "gallery/album_detail.html",
        {
            "album": album,
            "images": images,
        },
    )


@login_required
def delete_image(request, image_id):
    """
    Elimina uma imagem da base de dados e do Cloudinary.
    """
    image = get_object_or_404(GalleryImage, id=image_id)
    album_slug = image.album.slug

    if request.method != "POST":
        messages.error(request, "Pedido inválido.")
        return redirect("gallery:album_detail", slug=album_slug)

    try:
        public_id = getattr(image.image, "public_id", None)

        if public_id:
            destroy(public_id, invalidate=True, resource_type="image")

        image.delete()
        messages.success(request, "Foto eliminada com sucesso.")

    except Exception as error:
        messages.error(request, f"Não foi possível eliminar a foto. Erro: {error}")

    return redirect("gallery:album_detail", slug=album_slug)