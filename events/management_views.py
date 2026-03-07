from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
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
            p_paid=Count("participants", filter=Q(participants__is_paid=True), distinct=True),
            p_checked=Count("participants", filter=Q(participants__checked_in=True), distinct=True),
        )
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    paid = request.GET.get("paid", "")
    checkin = request.GET.get("checkin", "")

    if q:
        qs = qs.filter(
            Q(buyer_name__icontains=q)
            | Q(buyer_email__icontains=q)
            | Q(participants__full_name__icontains=q)
            | Q(participants__ticket_code__icontains=q)
        ).distinct()

    if paid == "1":
        qs = qs.filter(p_total__gt=0, p_paid=F("p_total"))
    elif paid == "0":
        qs = qs.filter(p_total__gt=0).exclude(p_paid=F("p_total"))

    if checkin == "1":
        qs = qs.filter(p_total__gt=0, p_checked=F("p_total"))
    elif checkin == "0":
        qs = qs.filter(p_total__gt=0).exclude(p_checked=F("p_total"))

    regs_base = Registration.objects.filter(event=event)
    parts_base = Participant.objects.filter(registration__event=event)

    kpi_total_regs = regs_base.count()
    kpi_total_participants = parts_base.count()
    kpi_total_paid_participants = parts_base.filter(is_paid=True).count()
    kpi_total_checkins = parts_base.filter(checked_in=True).count()
    kpi_pending_checkins = kpi_total_participants - kpi_total_checkins

    kpi_checkin_rate = 0
    if kpi_total_participants > 0:
        kpi_checkin_rate = round((kpi_total_checkins / kpi_total_participants) * 100)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "event": event,
        "page_obj": page_obj,
        "filters": {"q": q, "paid": paid, "checkin": checkin},
        "kpis": {
            "total_regs": kpi_total_regs,
            "total_paid_participants": kpi_total_paid_participants,
            "total_participants": kpi_total_participants,
            "total_checkins": kpi_total_checkins,
            "pending_checkins": kpi_pending_checkins,
            "checkin_rate": kpi_checkin_rate,
        },
    }
    return render(request, "management/event_registrations.html", context)


@login_required
@user_passes_test(can_manage_events)
@require_POST
def mark_registration_paid_full(request, reg_id):
    reg = get_object_or_404(Registration.objects.select_related("event"), pk=reg_id)
    now = timezone.now()

    reg.paid_amount = reg.total_price
    reg.is_paid = True
    reg.paid_at = now
    reg.save(update_fields=["paid_amount", "is_paid", "paid_at"])

    Participant.objects.filter(registration=reg).update(is_paid=True, paid_at=now)

    messages.success(request, "Pagamento total confirmado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_participant_paid(request, participant_id):
    p = get_object_or_404(Participant.objects.select_related("registration__event"), pk=participant_id)
    reg = p.registration
    event = reg.event
    price = event.price or Decimal("0.00")
    now = timezone.now()

    new_value = request.POST.get("value") == "1"

    p.mark_paid(new_value)
    p.save(update_fields=["is_paid", "paid_at"])

    if price > 0:
        if new_value:
            reg.paid_amount = min(reg.total_price, reg.paid_amount + price)
        else:
            reg.paid_amount = max(Decimal("0.00"), reg.paid_amount - price)

    all_paid = not Participant.objects.filter(registration=reg, is_paid=False).exists()
    reg.is_paid = all_paid
    reg.paid_at = now if all_paid else None
    reg.save(update_fields=["paid_amount", "is_paid", "paid_at"])

    messages.success(request, "Pagamento atualizado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_participant_checkin(request, participant_id):
    p = get_object_or_404(Participant.objects.select_related("registration__event"), pk=participant_id)

    if not p.is_paid and p.registration.event.price > 0:
        messages.error(request, "Não é possível fazer check-in sem pagamento confirmado.")
        return redirect(request.POST.get("next") or "events_mgmt:home")

    new_value = request.POST.get("value") == "1"
    p.mark_checked_in(new_value)
    p.save(update_fields=["checked_in", "checked_in_at"])

    messages.success(request, "Check-in atualizado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def checkin_all(request, reg_id):
    reg = get_object_or_404(
        Registration.objects.prefetch_related("participants").select_related("event"),
        pk=reg_id
    )

    if reg.event.price > 0 and reg.participants.filter(is_paid=False).exists():
        messages.error(request, "Ainda existem participantes por pagar.")
        return redirect(request.POST.get("next") or "events_mgmt:home")

    now = timezone.now()

    for p in reg.participants.all():
        if not p.checked_in:
            p.checked_in = True
            p.checked_in_at = now
            p.save(update_fields=["checked_in", "checked_in_at"])

    messages.success(request, "Check-in de todos os participantes registado.")
    return redirect(request.POST.get("next") or "events_mgmt:home")


@login_required
@user_passes_test(can_manage_events)
def scan_page(request):
    return render(request, "management/scan.html")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def scan_checkin_api(request):
    ticket_code = (request.POST.get("ticket_code") or "").strip()

    if not ticket_code:
        return JsonResponse(
            {
                "ok": False,
                "status": "invalid",
                "message": "Código do bilhete em falta.",
            },
            status=400,
        )

    participant = Participant.objects.select_related("registration__event").filter(
        ticket_code=ticket_code
    ).first()

    if not participant:
        return JsonResponse(
            {
                "ok": False,
                "status": "not_found",
                "message": "Bilhete não encontrado.",
                "ticket_code": ticket_code,
            },
            status=404,
        )

    event = participant.registration.event
    reg = participant.registration

    # se o pagamento ainda nao estiver confirmado, vai para a pagina do grupo
    if event.price > 0 and not participant.is_paid:
        return JsonResponse(
            {
                "ok": False,
                "status": "payment_pending",
                "message": "Pagamento ainda não confirmado.",
                "ticket_code": participant.ticket_code,
                "participant_name": participant.full_name or "(sem nome)",
                "event_title": event.title,
                "lookup_url": f"/gestao/inscricao/{reg.id}/grupo/",
            },
            status=409,
        )

    # se ja tiver feito check-in, fica no scanner e mostra aviso
    if participant.checked_in:
        return JsonResponse(
            {
                "ok": False,
                "status": "already_checked_in",
                "message": "Este participante já fez check-in.",
                "ticket_code": participant.ticket_code,
                "participant_name": participant.full_name or "(sem nome)",
                "event_title": event.title,
            },
            status=409,
        )

    participant.mark_checked_in(True)
    participant.save(update_fields=["checked_in", "checked_in_at"])

    return JsonResponse(
        {
            "ok": True,
            "status": "checked_in",
            "message": "Check-in confirmado com sucesso.",
            "ticket_code": participant.ticket_code,
            "participant_name": participant.full_name or "(sem nome)",
            "event_title": event.title,
            "checked_in_at": participant.checked_in_at.strftime("%H:%M") if participant.checked_in_at else "",
        }
    )

@login_required
@user_passes_test(can_manage_events)
def ticket_lookup(request, ticket_code):
    participant = get_object_or_404(
        Participant.objects.select_related("registration__event"),
        ticket_code=ticket_code,
    )

    return render(
        request,
        "management/ticket_lookup.html",
        {"participant": participant},
    )


@login_required
@user_passes_test(can_manage_events)
def registration_group(request, reg_id):
    reg = get_object_or_404(
        Registration.objects.select_related("event").prefetch_related("participants"),
        pk=reg_id,
    )

    participants = reg.participants.all()
    total_participants = participants.count()
    paid_participants = participants.filter(is_paid=True).count()
    checked_participants = participants.filter(checked_in=True).count()

    return render(
        request,
        "management/registration_group.html",
        {
            "reg": reg,
            "total_participants": total_participants,
            "paid_participants": paid_participants,
            "checked_participants": checked_participants,
        },
    )