from django import forms
from .models import Registration


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["buyer_name", "email", "phone", "ticket_qty", "payment_method"]

    def clean_ticket_qty(self):
        qty = self.cleaned_data["ticket_qty"]
        if qty < 1:
            raise forms.ValidationError("A quantidade de bilhetes deve ser pelo menos 1.")
        if qty > 20:
            raise forms.ValidationError("Máximo de 20 bilhetes por inscrição.")
        return qty