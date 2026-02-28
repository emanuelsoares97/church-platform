from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["buyer_name", "email", "phone", "ticket_qty", "payment_method"]
        widgets = {
            "buyer_name": forms.TextInput(attrs={"placeholder": "Ex: Emanuel Soares"}),
            "email": forms.EmailInput(attrs={"placeholder": "ex: nome@email.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "9xx xxx xxx"}),
            "ticket_qty": forms.NumberInput(attrs={"min": 1, "max": 20, "value": 1}),
            "payment_method": forms.RadioSelect(),
        }