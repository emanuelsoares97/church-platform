from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from events.forms import EventCreateForm
from events.models import Event
from management.permissions import leadership_required, reception_or_leadership_required


@reception_or_leadership_required
def events_list(request):
    """lista operacional de eventos para gestão."""
    events = (
        Event.objects.filter(is_archived=False)
        .annotate(reg_count=Count("registrations"))
        .order_by("-id")
    )
    return render(request, "management/events_list.html", {"events": events})


@leadership_required
def events_admin_list(request):
    """lista administrativa de eventos para edição e arquivamento."""
    archived = request.GET.get("archived") == "1"

    events = (
        Event.objects.filter(is_archived=archived)
        .annotate(reg_count=Count("registrations"))
        .order_by("-date", "-id")
    )
    return render(
        request,
        "management/events_admin_list.html",
        {
            "events": events,
            "show_archived": archived,
        },
    )


@reception_or_leadership_required
def create_event_view(request):
    """Permite criar eventos através da área de gestão."""
    if request.method == "POST":
        form = EventCreateForm(request.POST, request.FILES)

        if form.is_valid():
            event = form.save(commit=False)
            event.is_active = True
            event.save()

            messages.success(request, "Evento criado com sucesso.")
            return redirect("management:events_list")

        messages.error(request, "Verifica os campos do formulário.")
    else:
        form = EventCreateForm()

    return render(request, "management/create_event.html", {"form": form})


@reception_or_leadership_required
def edit_event_view(request, event_id):
    """Permite editar um evento através da área de gestão."""
    event = get_object_or_404(Event, pk=event_id)
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = EventCreateForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            form.save()
            messages.success(request, "Evento atualizado com sucesso.")
            return redirect(next_url or "management:events_admin_list")

        messages.error(request, "Verifica os campos do formulário.")
    else:
        form = EventCreateForm(instance=event)

    return render(
        request,
        "management/create_event.html",
        {
            "form": form,
            "is_edit": True,
            "event": event,
            "next_url": next_url,
        },
    )


@reception_or_leadership_required
@require_POST
def deactivate_event(request, event_id):
    """Desativa um evento, removendo-o da área pública."""
    event = get_object_or_404(Event, pk=event_id)
    event.is_active = False
    event.save(update_fields=["is_active"])

    messages.success(request, "Evento desativado com sucesso.")
    return redirect(request.POST.get("next") or "management:events_admin_list")


@reception_or_leadership_required
@require_POST
def activate_event(request, event_id):
    """Ativa um evento, tornando-o visível na área pública."""
    event = get_object_or_404(Event, pk=event_id)
    event.is_active = True
    event.save(update_fields=["is_active"])

    messages.success(request, "Evento ativado com sucesso.")
    return redirect(request.POST.get("next") or "management:events_admin_list")


@leadership_required
@require_POST
def archive_event(request, event_id):
    """Arquiva um evento na seção de histórico."""
    event = get_object_or_404(Event, pk=event_id)
    event.is_archived = True
    event.save(update_fields=["is_archived"])

    messages.success(request, "Evento arquivado com sucesso.")
    return redirect(request.POST.get("next") or "management:events_admin_list")


@leadership_required
@require_POST
def unarchive_event(request, event_id):
    """Retira um evento do arquivo na área de administração."""
    event = get_object_or_404(Event, pk=event_id)
    event.is_archived = False
    event.save(update_fields=["is_archived"])

    messages.success(request, "Evento desarquivado com sucesso.")
    return redirect(request.POST.get("next") or "management:events_admin_list")
