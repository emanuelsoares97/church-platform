import logging
from decimal import Decimal

from cloudinary.uploader import destroy
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from events.forms import EventCreateForm
from events.models import Event, Participant, Registration
from gallery.forms import GalleryAlbumForm
from gallery.models import GalleryAlbum, GalleryImage
from management.permissions import (
    leadership_required,
    management_required,
    media_or_leadership_required,
    reception_or_leadership_required,
)

from openpyxl import Workbook
from openpyxl.styles import Font
from management.services.registration_ops import (
    BulkCheckinNotAllowed,
    ParticipantCheckinNotAllowed,
    checkin_all as service_checkin_all,
    mark_registration_paid_full as service_mark_registration_paid_full,
    toggle_participant_checkin as service_toggle_participant_checkin,
    toggle_participant_paid as service_toggle_participant_paid,
)


logger = logging.getLogger(__name__)


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


@media_or_leadership_required
def gallery_albums_list(request):
    """Lista de álbuns para gestão com filtro por estado."""
    state = request.GET.get("estado", "todos")

    albums = GalleryAlbum.objects.all().order_by("-album_date", "-created_at")

    if state == "ativos":
        albums = albums.filter(is_active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
    elif state == "desativados":
        albums = albums.filter(is_active=False)
    elif state == "expirados":
        albums = albums.filter(is_active=True, expires_at__isnull=False, expires_at__lte=timezone.now())

    return render(
        request,
        "management/gallery_albums_list.html",
        {
            "albums": albums,
            "state": state,
        },
    )


@media_or_leadership_required
def management_album_detail(request, slug):
    """Mostra o detalhe de um álbum em contexto de gestão e permite upload de fotos."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    images = album.images.order_by("-uploaded_at")

    if request.method == "POST" and "images" in request.FILES:
        uploaded_files = request.FILES.getlist("images")

        if not uploaded_files:
            messages.error(request, "Seleciona pelo menos uma imagem.")
            return redirect("management:management_album_detail", slug=album.slug)

        for file in uploaded_files:
            GalleryImage.objects.create(
                album=album,
                image=file,
                uploaded_by=request.user,
            )

        messages.success(request, "Fotos adicionadas com sucesso.")
        return redirect("management:management_album_detail", slug=album.slug)

    return render(
        request,
        "management/album_management_detail.html",
        {
            "album": album,
            "images": images,
        },
    )


@media_or_leadership_required
def edit_gallery_album(request, slug):
    """Edita os campos de um álbum da galeria (título, descrição, data, retenção)."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    if request.method == "POST":
        form = GalleryAlbumForm(request.POST, instance=album)

        if form.is_valid():
            form.save()
            messages.success(request, "Álbum atualizado com sucesso.")
            return redirect("management:management_album_detail", slug=album.slug)

        messages.error(request, "Verifica os campos do formulário.")
    else:
        form = GalleryAlbumForm(instance=album)

    return render(
        request,
        "management/edit_gallery_album.html",
        {
            "form": form,
            "album": album,
        },
    )


@media_or_leadership_required
@require_POST
def deactivate_gallery_album(request, slug):
    """Desativa um álbum, removendo-o da área pública."""
    album = get_object_or_404(GalleryAlbum, slug=slug)
    album.is_active = False
    album.save(update_fields=["is_active"])

    messages.success(request, "Álbum desativado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")


@media_or_leadership_required
@require_POST
def activate_gallery_album(request, slug):
    """Ativa um álbum, tornando-o visível na área pública."""
    album = get_object_or_404(GalleryAlbum, slug=slug)
    album.is_active = True
    album.save(update_fields=["is_active"])

    messages.success(request, "Álbum ativado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")


@media_or_leadership_required
@require_POST
def delete_gallery_album(request, slug):
    """Elimina definitivamente um álbum da gestão e da base de dados."""
    album = get_object_or_404(GalleryAlbum, slug=slug)

    for image in album.images.all():
        public_id = getattr(image.image, "public_id", None)
        if public_id:
            try:
                destroy(public_id, invalidate=True, resource_type="image")
            except Exception as error:
                # Mantemos a eliminação do álbum mesmo se um ficheiro remoto falhar.
                logger.warning(
                    "Falha ao eliminar imagem no Cloudinary durante eliminação do álbum",
                    extra={
                        "album_id": album.id,
                        "album_slug": album.slug,
                        "public_id": public_id,
                        "error": str(error),
                    },
                )

    album.delete()
    messages.success(request, "Álbum eliminado com sucesso.")
    return redirect(request.POST.get("next") or "management:gallery_albums_list")


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

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "event": event,
        "page_obj": page_obj,
        "filters": {"q": q, "paid": paid, "checkin": checkin},
        "kpis": build_event_kpis(event),
    }
    return render(request, "management/event_registrations.html", context)


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


@reception_or_leadership_required
@require_POST
def mark_registration_paid_full(request, reg_id):
    """marca toda a inscrição como paga (todos os participantes)."""
    reg = get_object_or_404(Registration.objects.select_related("event"), pk=reg_id)
    result = service_mark_registration_paid_full(reg)

    is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

    if not is_ajax:
        messages.success(request, "Pagamento total confirmado")

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message": "Pagamento total confirmado",
                "kpis": build_event_kpis(result.event),
            }
        )

    return redirect(request.POST.get("next") or "management:home")


@reception_or_leadership_required
@require_POST
def toggle_participant_paid(request, participant_id):
    """alterna status de pagamento de um participante específico."""
    p = get_object_or_404(
        Participant.objects.select_related("registration__event"),
        pk=participant_id,
    )
    new_value = request.POST.get("value") == "1"
    result = service_toggle_participant_paid(p, new_value=new_value)
    reg = result.registration
    event = result.event
    participant = result.participant

    is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

    if not is_ajax:
        messages.success(request, "Pagamento atualizado")

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message": "Pagamento atualizado",
                "kpis": build_event_kpis(event),
                "participant": {
                    "id": participant.id,
                    "is_paid": participant.is_paid,
                    "checked_in": participant.checked_in,
                },
                "registration": {
                    "id": reg.id,
                    "is_paid": reg.is_paid,
                    "paid_amount": str(reg.paid_amount),
                },
            }
        )

    return redirect(request.POST.get("next") or "management:home")


@reception_or_leadership_required
@require_POST
def toggle_participant_checkin(request, participant_id):
    """alterna status de check-in de um participante (bloqueado se não pago)."""
    p = get_object_or_404(
        Participant.objects.select_related("registration__event"),
        pk=participant_id,
    )
    event = p.registration.event

    is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

    new_value = request.POST.get("value") == "1"

    try:
        result = service_toggle_participant_checkin(p, new_value=new_value)
        participant = result.participant
    except ParticipantCheckinNotAllowed:
        if not is_ajax:
            messages.error(request, "Não é possível fazer check-in sem pagamento confirmado")

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Não é possível fazer check-in sem pagamento confirmado",
                    "kpis": build_event_kpis(event),
                },
                status=400,
            )

        return redirect(request.POST.get("next") or "management:home")

    if not is_ajax:
        messages.success(request, "Check-in atualizado")

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message": "Check-in atualizado",
                "kpis": build_event_kpis(event),
                "participant": {
                    "id": participant.id,
                    "is_paid": participant.is_paid,
                    "checked_in": participant.checked_in,
                },
            }
        )

    return redirect(request.POST.get("next") or "management:home")


@reception_or_leadership_required
@require_POST
def checkin_all(request, reg_id):
    """faz check-in de todos os participantes da inscrição (se pagos)."""
    reg = get_object_or_404(
        Registration.objects.prefetch_related("participants").select_related("event"),
        pk=reg_id,
    )
    event = reg.event

    is_ajax = request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

    try:
        service_checkin_all(reg)
    except BulkCheckinNotAllowed:
        if not is_ajax:
            messages.error(request, "Ainda existem participantes por pagar")

        if is_ajax:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Ainda existem participantes por pagar",
                    "kpis": build_event_kpis(event),
                },
                status=400,
            )

        return redirect(request.POST.get("next") or "management:home")

    if not is_ajax:
        messages.success(request, "Check-in de todos os participantes registado")

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message": "Check-in de todos os participantes registado",
                "kpis": build_event_kpis(event),
            }
        )

    return redirect(request.POST.get("next") or "management:home")


@management_required
def scan_page(request):
    """página do scanner qr para check-in rápido."""
    return render(request, "management/scan.html")


@management_required
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


@management_required
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


@management_required
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
            "kpis": build_event_kpis(reg.event),
        },
    )


@leadership_required
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


@leadership_required
def reports(request):
    """lista de eventos para acesso rápido aos relatórios."""
    events = (
        Event.objects.all()
        .annotate(reg_count=Count("registrations"))
        .order_by("-id")
    )
    return render(request, "management/reports.html", {"events": events})


@leadership_required
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