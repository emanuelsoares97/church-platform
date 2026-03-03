from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, Participant
from .forms import RegistrationForm
from django.utils import timezone
from .models import Event, Registration
from django.db import transaction
from events.services.emails import send_registration_tickets_email

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

            if event.price == 0:
                registration.is_paid= True
                registration.paid_at = timezone.now()

            registration.save()
            transaction.on_commit(lambda: send_registration_tickets_email(registration.id))

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

            Participant.objects.bulk_create(
                [Participant(registration=registration, full_name=name) for name in cleaned_names]
            )

            messages.success(request, "Inscrição registada com sucesso!")
            return redirect(
                "events:registration_success",
                slug=event.slug,
                public_id=registration.public_id,
            )

        # se o form for inválido, mantém participantes e mostra erros
        messages.error(request, "Há campos inválidos. Corrige e tenta novamente.")
        return render(
            request,
            "events/event_detail.html",
            {"event": event, "form": form, "participant_values": participant_names},
        )

    # GET
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