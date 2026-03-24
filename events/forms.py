from django import forms

from core.utils.images import optimize_uploaded_image
from .models import Event, Registration


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["buyer_name", "buyer_email", "phone", "ticket_qty", "payment_method"]
        widgets = {
            "buyer_name": forms.TextInput(attrs={"placeholder": "Ex: Emanuel Soares"}),
            "buyer_email": forms.EmailInput(attrs={"placeholder": "ex: nome@email.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "9xx xxx xxx"}),
            "ticket_qty": forms.NumberInput(attrs={"min": 1, "max": 20, "value": 1}),
            "payment_method": forms.RadioSelect(),
        }


class EventAdminForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = "__all__"

    def clean_banner_image(self):
        image = self.cleaned_data.get("banner_image")

        if not image:
            return image

        return optimize_uploaded_image(image)


class EventCreateForm(forms.ModelForm):
    """Formulário para criação de eventos na área de gestão."""

    ticket_qty = forms.IntegerField(
        min_value=1,
        initial=1,
        required=False,
        label="Número de bilhetes (planeamento)",
        help_text="Nao limita inscricoes automaticamente.",
    )

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "banner_image",
            "date",
            "location",
            "price",
            "registration_deadline",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Conferência Jovem"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Descrição opcional do evento"}),
            "banner_image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "location": forms.TextInput(attrs={"placeholder": "Ex.: Auditório Principal"}),
            "price": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
            "registration_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        labels = {
            "title": "Título",
            "description": "Descrição",
            "banner_image": "Banner do evento",
            "date": "Data do evento",
            "location": "Local",
            "price": "Preço",
            "registration_deadline": "Inscrições abertas até",
        }

    def clean_banner_image(self):
        image = self.cleaned_data.get("banner_image")

        if not image:
            return image

        return optimize_uploaded_image(image)

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get("date")
        deadline = cleaned_data.get("registration_deadline")

        if event_date and deadline and deadline.date() > event_date:
            self.add_error(
                "registration_deadline",
                "O prazo de inscricao nao pode ser depois da data do evento.",
            )

        return cleaned_data