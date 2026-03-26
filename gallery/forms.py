from django import forms

from core.utils.images import optimize_uploaded_image
from .models import GalleryAlbum, GalleryImage


class GalleryAlbumForm(forms.ModelForm):
    """
    Formulário para criação e edição de álbuns.
    """

    class Meta:
        model = GalleryAlbum
        fields = [
            "title",
            "description",
            "album_date",
            "retention_days",
        ]
        labels = {
            "retention_days": "Disponibilidade pública",
        }
        help_texts = {
            "retention_days": (
                "Escolha durante quanto tempo o álbum fica visível no público. "
                "A opção 'Sempre disponível' só deixa de estar pública se desativar "
                "ou eliminar manualmente."
            ),
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Culto Domingo"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Descrição opcional do álbum"}),
            "album_date": forms.DateInput(attrs={"type": "date"}),
        }


class GalleryImageForm(forms.ModelForm):
    """
    Formulário para upload de imagens da galeria.

    Aplica otimização automática antes do upload final.
    """

    class Meta:
        model = GalleryImage
        fields = ["image"]

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        try:
            image = optimize_uploaded_image(image)
        except Exception:
            raise forms.ValidationError(
                "Erro ao processar a imagem. Tente outra imagem."
            )

        return image