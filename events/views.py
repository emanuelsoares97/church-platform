from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import RegistrationForm
from .models import Event, Registration, Participant
from events.services.emails import send_registration_tickets_email


def make_ticket_code(registration: Registration, idx: int) -> str:
    base = str(registration.public_id).replace("-", "")[:8].upper()
    year = registration.created_at.year
    return f"EVT-{year}-{base}-P{idx:02d}"


def event_list(request):
    events = Event.objects.filter(is_active=True).order_by("date")
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)

    if request.method == "POST":
        form = RegistrationForm(request.POST)
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
                    {"event": event, "form": form, "participant_values": participant_names},
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

            # se for grátis, fica tudo pago
            if is_free:
                registration.paid_amount = registration.total_price  # 0.00
                registration.is_paid = True
                registration.paid_at = now
                registration.save(update_fields=["paid_amount", "is_paid", "paid_at"])

            # envia os bilhetes por email
            transaction.on_commit(lambda: send_registration_tickets_email(registration.id))

            messages.success(request, "Inscrição registada com sucesso!")
            return redirect(
                "events:registration_success",
                slug=event.slug,
                public_id=registration.public_id,
            )

        messages.error(request, "Há campos inválidos. Corrige e tenta novamente.")
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "form": form, "participant_values": participant_names},
        )

    form = RegistrationForm()
    return render(
        request,
        "events/event_detail.html",
        {"event": event, "form": form, "participant_values": []},
    )


def registration_success(request, slug, public_id):
    event = get_object_or_404(Event, slug=slug, is_active=True)

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