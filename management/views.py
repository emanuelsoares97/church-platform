from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from events.models import Event, Registration, Participant
from events.permissions import can_manage_events
from openpyxl import Workbook
from openpyxl.styles import Font


@login_required
@user_passes_test(can_manage_events)
def dashboard(request):
    """home da gestão (hub principal)."""
    return render(request, "management/dashboard.html")

def build_event_kpis(event):
    """Calcula os KPIs principais de um evento para a área de gestão."""
    regs_base = Registration.objects.filter(event=event)
    parts_base = Participant.objects.filter(registration__event=event)

    total_regs = regs_base.count()
    total_participants = parts_base.count()
    total_paid_participants = parts_base.filter(is_paid=True).count()
    total_checkins = parts_base.filter(checked_in=True).count()
    pending_checkins = total_participants - total_checkins

    checkin_rate = 0
    if total_participants > 0:
        checkin_rate = round((total_checkins / total_participants) * 100)

    return {
        "total_regs": total_regs,
        "total_paid_participants": total_paid_participants,
        "total_participants": total_participants,
        "total_checkins": total_checkins,
        "pending_checkins": pending_checkins,
        "checkin_rate": checkin_rate,
    }

@login_required
@user_passes_test(can_manage_events)
def events_list(request):
    """lista de eventos para gestão."""
    events = (
        Event.objects.all()
        .annotate(reg_count=Count("registrations"))
        .order_by("-id")
    )
    return render(request, "management/events_list.html", {"events": events})


@login_required
@user_passes_test(can_manage_events)
def event_registrations(request, event_id):
    """lista inscrições de um evento com filtros e paginação."""
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
    """marca toda a inscrição como paga (todos os participantes)."""
    reg = get_object_or_404(Registration.objects.select_related("event"), pk=reg_id)
    now = timezone.now()

    reg.paid_amount = reg.total_price
    reg.is_paid = True
    reg.paid_at = now
    reg.save(update_fields=["paid_amount", "is_paid", "paid_at"])

    Participant.objects.filter(registration=reg).update(is_paid=True, paid_at=now)

    messages.success(request, "Pagamento total confirmado")
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.POST.get("next") or "management:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_participant_paid(request, participant_id):
    """alterna status de pagamento de um participante específico."""
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

    messages.success(request, "Pagamento atualizado")
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.POST.get("next") or "management:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def toggle_participant_checkin(request, participant_id):
    """alterna status de check-in de um participante (bloqueado se não pago)."""
    p = get_object_or_404(Participant.objects.select_related("registration__event"), pk=participant_id)

    if not p.is_paid and p.registration.event.price > 0:
        messages.error(request, "Não é possível fazer check-in sem pagamento confirmado")
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Não é possível fazer check-in sem pagamento confirmado"})
        return redirect(request.POST.get("next") or "management:home")

    new_value = request.POST.get("value") == "1"
    p.mark_checked_in(new_value)
    p.save(update_fields=["checked_in", "checked_in_at"])

    messages.success(request, "Check-in atualizado")
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.POST.get("next") or "management:home")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def checkin_all(request, reg_id):
    """faz check-in de todos os participantes da inscrição (se pagos)."""
    reg = get_object_or_404(
        Registration.objects.prefetch_related("participants").select_related("event"),
        pk=reg_id
    )

    if reg.event.price > 0 and reg.participants.filter(is_paid=False).exists():
        messages.error(request, "Ainda existem participantes por pagar")
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "Ainda existem participantes por pagar"})
        return redirect(request.POST.get("next") or "management:home")

    now = timezone.now()

    for p in reg.participants.all():
        if not p.checked_in:
            p.checked_in = True
            p.checked_in_at = now
            p.save(update_fields=["checked_in", "checked_in_at"])

    messages.success(request, "Check-in de todos os participantes registado")
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(request.POST.get("next") or "management:home")


@login_required
@user_passes_test(can_manage_events)
def scan_page(request):
    """página do scanner qr para check-in rápido."""
    return render(request, "management/scan.html")


@login_required
@user_passes_test(can_manage_events)
@require_POST
def scan_checkin_api(request):
    """api para check-in via scanner qr (valida código e faz check-in)."""
    ticket_code = (request.POST.get("ticket_code") or "").strip()

    if not ticket_code:
        return JsonResponse(
            {
                "ok": False,
                "status": "invalid",
                "message": "Código do bilhete em falta",
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
                "message": "Bilhete não encontrado",
                "ticket_code": ticket_code,
            },
            status=404,
        )

    event = participant.registration.event
    reg = participant.registration

    # se o pagamento ainda não estiver confirmado vai para a página do grupo
    if event.price > 0 and not participant.is_paid:
        return JsonResponse(
            {
                "ok": False,
                "status": "payment_pending",
                "message": "Pagamento ainda não confirmado",
                "ticket_code": participant.ticket_code,
                "participant_name": participant.full_name or "(sem nome)",
                "event_title": event.title,
                "lookup_url": f"/gestao/inscricao/{reg.id}/grupo/",
            },
            status=409,
        )

    # se já tiver feito check-in fica no scanner e mostra aviso
    if participant.checked_in:
        return JsonResponse(
            {
                "ok": False,
                "status": "already_checked_in",
                "message": "Este participante já fez check-in",
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
            "message": "Check-in confirmado com sucesso",
            "ticket_code": participant.ticket_code,
            "participant_name": participant.full_name or "(sem nome)",
            "event_title": event.title,
            "checked_in_at": participant.checked_in_at.strftime("%H:%M") if participant.checked_in_at else "",
        }
    )

@login_required
@user_passes_test(can_manage_events)
def ticket_lookup(request, ticket_code):
    """busca participante por código do bilhete."""
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
    """página detalhada de um grupo de participantes."""
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

@login_required
def export_event_registrations_excel(request, event_id):
    """
    Exporta para Excel os participantes de um evento.

    Gera um ficheiro .xlsx com os dados principais do evento,
    comprador, participante, pagamento e check-in.
    """
    # obtém o evento pretendido
    event = get_object_or_404(Event, id=event_id)

    # obtém todos os participantes ligados ao evento
    # usa select_related para evitar queries desnecessárias
    participants = (
        Participant.objects
        .filter(registration__event=event)
        .select_related("registration", "registration__event")
        .order_by("registration__created_at", "id")
    )

    # cria o workbook e a folha principal
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inscrições"

    # cabeçalhos da folha
    headers = [
        "Evento",
        "Data do evento",
        "Comprador",
        "Email do comprador",
        "Participante",
        "Código do bilhete",
        "Pago",
        "Pago em",
        "Check-in",
        "Check-in em",
        "Data da inscrição",
    ]

    # escreve os cabeçalhos
    worksheet.append(headers)

    # aplica estilo simples ao cabeçalho
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    # escreve uma linha por participante
    for participant in participants:
        registration = participant.registration

        worksheet.append([
            event.title,
            event.date.strftime("%d/%m/%Y %H:%M") if event.date else "",
            registration.buyer_name,
            registration.buyer_email,
            participant.full_name,
            participant.ticket_code,
            "Sim" if participant.is_paid else "Não",
            participant.paid_at.strftime("%d/%m/%Y %H:%M") if participant.paid_at else "",
            "Sim" if participant.checked_in else "Não",
            participant.checked_in_at.strftime("%d/%m/%Y %H:%M") if participant.checked_in_at else "",
            registration.created_at.strftime("%d/%m/%Y %H:%M") if registration.created_at else "",
        ])

    # ajusta larguras de coluna de forma simples
    column_widths = {
        "A": 30,
        "B": 20,
        "C": 28,
        "D": 35,
        "E": 28,
        "F": 22,
        "G": 10,
        "H": 20,
        "I": 10,
        "J": 20,
        "K": 20,
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    # cria a resposta http com o ficheiro excel
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # cria nome seguro para o ficheiro
    safe_title = event.slug if getattr(event, "slug", None) else f"evento-{event.id}"
    response["Content-Disposition"] = (
        f'attachment; filename="inscricoes-{safe_title}.xlsx"'
    )

    # grava o workbook na resposta
    workbook.save(response)

    return response

@login_required
@user_passes_test(can_manage_events)
def reports(request):
    """lista de eventos para acesso rápido aos relatórios."""
    events = (
        Event.objects.all()
        .annotate(reg_count=Count("registrations"))
        .order_by("-id")
    )
    return render(request, "management/reports.html", {"events": events})


@login_required
@user_passes_test(can_manage_events)
def event_report(request, event_id):
    """relatório resumido de um evento."""
    event = get_object_or_404(Event, pk=event_id)

    registrations = Registration.objects.filter(event=event)
    participants = Participant.objects.filter(registration__event=event)

    total_regs = registrations.count()
    total_participants = participants.count()
    total_paid = participants.filter(is_paid=True).count()
    total_checkins = participants.filter(checked_in=True).count()

    price = event.price or Decimal("0.00")
    expected_amount = price * total_participants
    received_amount = price * total_paid
    pending_amount = expected_amount - received_amount

    checkin_rate = 0
    if total_participants > 0:
        checkin_rate = round((total_checkins / total_participants) * 100)

    paid_rate = 0
    if total_participants > 0:
        paid_rate = round((total_paid / total_participants) * 100)

    context = {
        "event": event,
        "report": {
            "total_regs": total_regs,
            "total_participants": total_participants,
            "total_paid": total_paid,
            "total_checkins": total_checkins,
            "expected_amount": expected_amount,
            "received_amount": received_amount,
            "pending_amount": pending_amount,
            "checkin_rate": checkin_rate,
            "paid_rate": paid_rate,
        },
    }
    return render(request, "management/event_report.html", context)