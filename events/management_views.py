from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Event, Registration, Participant
from .permissions import can_manage_events


@login_required
@user_passes_test(can_manage_events)
def dashboard_home(request):
    events = (
        Event.objects.all()
        .annotate(reg_count=Count("registrations"))
        .order_by("-id")
    )
    return render(request, "management/home.html", {"events": events})


@login_required
@user_passes_test(can_manage_events)
def event_registrations(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    qs = (
        Registration.objects.filter(event=event)
    .select_related("event")
    .prefetch_related("participants")
    .annotate(
        p_total=Count("participants", distinct=True),
        p_checked=Count("participants", filter=Q(participants__checked_in=True), distinct=True),
    )
    .order_by("-created_at")
)

    q = request.GET.get("q", "").strip()
    paid = request.GET.get("paid", "")
    checkin = request.GET.get("checkin", "")  # "1" completo, "0" nenhum

    if q:
        qs = qs.filter(
            Q(buyer_name__icontains=q)
            | Q(buyer_email__icontains=q)
            | Q(participants__full_name__icontains=q)
        ).distinct()

    if paid in {"0", "1"}:
        qs = qs.filter(is_paid=(paid == "1"))

    if checkin == "1":
        qs = qs.filter(p_total__gt=0, p_checked=F("p_total"))
    elif checkin == "0":
        qs = qs.filter(p_checked=0)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "event": event,
        "page_obj": page_obj,
        "filters": {"q": q, "paid": paid, "checkin": checkin},
    }
    return render(request, "management/event_registrations.html", context)


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_paid(request, reg_id):
    reg = get_object_or_404(Registration, pk=reg_id)
    new_value = request.POST.get("value") == "1"
    reg.mark_paid(new_value)
    reg.save(update_fields=["is_paid", "paid_at"])
    messages.success(request, "Pagamento atualizado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_participant_checkin(request, participant_id):
    p = get_object_or_404(Participant, pk=participant_id)

    # não permite check-in se não estiver pago
    if not p.registration.is_paid:
        messages.error(request, "Não é possível fazer check-in sem pagamento confirmado.")
        return redirect(request.POST.get("next") or "events_mgmt:home")

    new_value = request.POST.get("value") == "1"
    p.mark_checked_in(new_value)
    p.save(update_fields=["checked_in", "checked_in_at"])

    messages.success(request, "Check-in do participante atualizado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")