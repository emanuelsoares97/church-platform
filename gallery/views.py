from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import GalleryImageForm
from .models import GalleryAlbum, GalleryImage


def album_list(request):
    """
    Mostra a lista de álbuns ativos e não expirados.
    """
    albums = (
        GalleryAlbum.objects.filter(is_active=True, expires_at__gt=timezone.now())
        .prefetch_related("images")
        .order_by("-created_at")
    )

    return render(
        request,
        "gallery/album_list.html",
        {
            "albums": albums,
        },
    )


def album_detail(request, slug):
    """
    Mostra o detalhe de um álbum e permite upload de imagens
    a utilizadores autenticados.
    """
    album = get_object_or_404(
        GalleryAlbum.objects.prefetch_related("images"),
        slug=slug,
        is_active=True,
        expires_at__gt=timezone.now(),
    )

    form = GalleryImageForm()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Precisas de iniciar sessão para adicionar fotos.")
            return redirect("login")

        images = request.FILES.getlist("images")

        if not images:
            messages.error(request, "Seleciona pelo menos uma imagem.")
            return redirect("gallery:album_detail", slug=album.slug)

        for image in images:
            GalleryImage.objects.create(
                album=album,
                image=image,
                uploaded_by=request.user,
            )

        messages.success(request, f"{len(images)} fotos adicionadas à galeria.")
        return redirect("gallery:album_detail", slug=album.slug)

    return render(
        request,
        "gallery/album_detail.html",
        {
            "album": album,
            "images": album.images.all(),
            "form": form,
        },
    )