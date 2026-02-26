from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event, Participant
from .forms import RegistrationForm


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

            # Criar participants com base na quantidade e nomes recebidos
            qty = registration.ticket_qty

            # Garantir que temos nomes suficientes 
            cleaned_names = [n.strip() for n in participant_names if n.strip()]
            if len(cleaned_names) != qty:
                registration.delete()
                messages.error(
                    request,
                    f"Precisas preencher exatamente {qty} nome(s) de participante."
                )
                return redirect("events:event_detail", slug=event.slug)

            Participant.objects.bulk_create(
                [Participant(registration=registration, full_name=name) for name in cleaned_names]
            )

            messages.success(request, "Inscrição registada com sucesso!")
            return redirect("events:event_detail", slug=event.slug)

    else:
        form = RegistrationForm()

    return render(request, "events/event_detail.html", {"event": event, "form": form})