from __future__ import annotations

import threading

from django.db import transaction
from django.utils import timezone

from events.models import Participant, Registration
from events.services.emails import send_registration_tickets_email


class RegistrationCreationError(Exception):
    """Erro de validação de negócio no fluxo de inscrição pública."""


def make_ticket_code(registration: Registration, idx: int) -> str:
    """Gera código único para participante baseado na inscrição."""
    base = str(registration.public_id).replace("-", "")[:8].upper()
    year = registration.created_at.year
    return f"EVT-{year}-{base}-P{idx:02d}"


def create_public_registration(*, event, form, participant_names: list[str]) -> Registration:
    """Cria inscrição pública completa, participantes e pós-processamento.

    Mantém o comportamento atual:
    - valida número de participantes por ticket_qty
    - marca pago automaticamente quando evento é gratuito
    - agenda envio de email no on_commit
    """
    with transaction.atomic():
        registration = form.save(commit=False)
        registration.event = event
        registration.save()

        qty = registration.ticket_qty
        cleaned_names = [name.strip() for name in participant_names if name.strip()]

        if len(cleaned_names) != qty:
            raise RegistrationCreationError(
                f"Precisas preencher exatamente {qty} nome(s) de participante."
            )

        now = timezone.now()
        is_free = event.price == 0

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

        if is_free:
            registration.paid_amount = registration.total_price
            registration.is_paid = True
            registration.paid_at = now
            registration.save(update_fields=["paid_amount", "is_paid", "paid_at"])

        transaction.on_commit(
            lambda: threading.Thread(
                target=send_registration_tickets_email,
                args=(registration.id,),
                daemon=True,
            ).start()
        )

        return registration