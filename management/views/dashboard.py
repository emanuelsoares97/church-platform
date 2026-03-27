from django.shortcuts import render

from management.permissions import (
    management_required,
    media_or_leadership_required,
    reception_or_leadership_required,
)


@management_required
def dashboard(request):
    """home da gestão (hub principal)."""
    return render(request, "management/dashboard.html")


@reception_or_leadership_required
def events_hub(request):
    """Página intermédia para ações de gestão de eventos."""
    return render(request, "management/events_hub.html")


@media_or_leadership_required
def gallery_hub(request):
    """Página intermédia para ações de gestão da galeria."""
    return render(request, "management/gallery_hub.html")
