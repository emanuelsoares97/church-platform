from django.shortcuts import render
from events.models import Event


def home(request):
    """página principal do site."""
    featured_events = Event.objects.filter(is_active=True).order_by("date")[:3]

    context = {
        "featured_events": featured_events,
    }
    return render(request, "core/home.html", context)
