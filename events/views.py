from io import BytesIO
import threading

import qrcode
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import RegistrationForm
from .models import Event, Registration, Participant
from events.services.emails import send_registration_tickets_email


def make_ticket_code(registration: Registration, idx: int) -> str:
    """gera código único para participante baseado na inscrição."""
    base = str(registration.public_id).replace("-", "")[:8].upper()
    year = registration.created_at.year
    return f"EVT-{year}-{base}-P{idx:02d}"


def event_list(request):
    """lista eventos ativos para inscrição pública."""
    Event.archive_past_events()
    events = Event.objects.filter(is_active=True, is_archived=False).order_by("date")
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, slug):
    """página do evento com formulário de inscrição."""
    Event.archive_past_events()
    event = get_object_or_404(Event, slug=slug, is_active=True, is_archived=False)
    registration_open = event.is_registration_open()

    if request.method == "POST" and not registration_open:
        messages.error(request, "As inscrições para este evento já se encontram encerradas.")
        return redirect("events:event_detail", slug=event.slug)

    if request.method == "POST":
        post_data = request.POST.copy()

        if event.price == 0 and not post_data.get("payment_method"):
            post_data["payment_method"] = "LOCAL"

        form = RegistrationForm(post_data)
        participant_names = request.POST.getlist("participant_name")

        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.save()

            qty = registration.ticket_qty
            cleaned_names = [n.strip() for n in participant_names if n.strip()]

            if len(cleaned_names) != qty:
                registration.delete()
                messages.error(request, f"Precisas preencher exatamente {qty} nome(s) de participante.")
                return render(
                    request,
                    "events/event_detail.html",
                    {
                        "event": event,
                        "form": form,
                        "participant_values": participant_names,
                        "registration_open": registration_open,
                    },
                )

            now = timezone.now()
            is_free = (event.price == 0)

            participants_to_create = []
            for idx, name in enumerate(cleaned_names, start=1):
                participants_to_create.append(
                    Participant(
                        registration=registration,
                        full_name=name,
                        ticket_code=make_ticket_code(registration, idx),
                        is_paid=is_free,
                        paid_at=now if is_free else None,
                    )
                )

            Participant.objects.bulk_create(participants_to_create)

            # se for grátis fica tudo pago
            if is_free:
                registration.paid_amount = registration.total_price
                registration.is_paid = True
                registration.paid_at = now
                registration.save(update_fields=["paid_amount", "is_paid", "paid_at"])

            # envia os bilhetes por email
            transaction.on_commit(
                lambda: threading.Thread(
                    target=send_registration_tickets_email,
                    args=(registration.id,),
                    daemon=True,
                ).start()
            )

            messages.success(request, "Inscrição registada com sucesso")
            return redirect(
                "events:registration_success",
                slug=event.slug,
                public_id=registration.public_id,
            )

        messages.error(request, "Há campos inválidos. Corrige e tenta novamente")
        return render(
            request,
            "events/event_detail.html",
            {
                "event": event,
                "form": form,
                "participant_values": participant_names,
                "registration_open": registration_open,
            },
        )

    form = RegistrationForm()
    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "form": form,
            "participant_values": [],
            "registration_open": registration_open,
        },
    )


def registration_success(request, slug, public_id):
    """página de confirmação após inscrição bem-sucedida."""
    Event.archive_past_events()
    event = get_object_or_404(Event, slug=slug, is_active=True, is_archived=False)

    registration = get_object_or_404(
        Registration.objects.select_related("event").prefetch_related("participants"),
        event=event,
        public_id=public_id,
    )

    context = {
        "event": event,
        "registration": registration,
        "participants": registration.participants.all(),
    }
    return render(request, "events/registration_success.html", context)


def ticket_qr_image(request, ticket_code):
    """gera o qr code do participante e devolve como imagem png."""
    participant = get_object_or_404(Participant, ticket_code=ticket_code)

    qr_target = f"{settings.SITE_URL}/gestao/t/{participant.ticket_code}/"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_target)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")
