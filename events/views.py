from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import RegistrationForm
from .models import Event, Registration, Participant
from events.services.registrations import (
    RegistrationCreationError,
    create_public_registration,
    make_ticket_code as _make_ticket_code,
)


def make_ticket_code(registration: Registration, idx: int) -> str:
    """Compat wrapper: mantém import estável para código/testes legados."""
    return _make_ticket_code(registration, idx)


def event_list(request):
    """lista eventos ativos na área pública."""
    today = timezone.now().date()

    events = (
        Event.objects.filter(
            is_active=True,
            is_archived=False,
            date__gte=today,
        )
        .order_by("date")
    )
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, slug):
    """página do evento com formulário de inscrição."""
    today = timezone.now().date()
    event = get_object_or_404(
        Event,
        slug=slug,
        is_active=True,
        is_archived=False,
        date__gte=today,
    )

    registration_open = event.can_accept_registrations()

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
            try:
                registration = create_public_registration(
                    event=event,
                    form=form,
                    participant_names=participant_names,
                )
            except RegistrationCreationError as error:
                messages.error(request, str(error))
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
    event = get_object_or_404(Event, slug=slug)

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