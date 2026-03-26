from django.http import JsonResponse
from django.shortcuts import render
from events.models import Event
from core.data.ministries import MINISTRIES


def home(request):
    """página principal do site."""
    featured_events = Event.objects.filter(is_active=True).order_by("date")[:3]

    context = {
        "featured_events": featured_events,
    }
    return render(request, "core/home.html", context)

def about(request):
    return render(request, "core/about.html")


def ministerios(request):
    """página pública com as áreas/ministérios da igreja."""
    context = {
        "ministries": MINISTRIES,
    }
    return render(request, "core/ministries.html", context)


def ministry_kids(request):
    """página pública do ministério Kids."""
    return render(request, "core/ministries_kids.html")


def ministry_young(request):
    """página pública do ministério Jovens."""
    return render(request, "core/ministries_young.html")

def contacts(request):
    return render(request, "core/contacts.html")


def healthcheck(request):
    """Endpoint simples para verificação de saúde da aplicação."""
    return JsonResponse({"status": "ok"})