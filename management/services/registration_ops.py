from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from events.models import Participant, Registration


class ParticipantCheckinNotAllowed(Exception):
    """Não é permitido check-in do participante no estado atual."""


class BulkCheckinNotAllowed(Exception):
    """Não é permitido check-in em massa no estado atual."""


@dataclass
class RegistrationOpResult:
    event: object
    registration: Registration
    participant: Participant | None = None


def mark_registration_paid_full(registration: Registration) -> RegistrationOpResult:
    now = timezone.now()

    with transaction.atomic():
        registration.paid_amount = registration.total_price
        registration.is_paid = True
        registration.paid_at = now
        registration.save(update_fields=["paid_amount", "is_paid", "paid_at"])

        Participant.objects.filter(registration=registration).update(is_paid=True, paid_at=now)

    return RegistrationOpResult(event=registration.event, registration=registration)


def toggle_participant_paid(participant: Participant, *, new_value: bool) -> RegistrationOpResult:
    registration = participant.registration
    event = registration.event
    price = event.price or Decimal("0.00")
    now = timezone.now()

    with transaction.atomic():
        participant.mark_paid(new_value)
        participant.save(update_fields=["is_paid", "paid_at"])

        if price > 0:
            if new_value:
                registration.paid_amount = min(registration.total_price, registration.paid_amount + price)
            else:
                registration.paid_amount = max(Decimal("0.00"), registration.paid_amount - price)

        all_paid = not Participant.objects.filter(registration=registration, is_paid=False).exists()
        registration.is_paid = all_paid
        registration.paid_at = now if all_paid else None
        registration.save(update_fields=["paid_amount", "is_paid", "paid_at"])

    return RegistrationOpResult(
        event=event,
        registration=registration,
        participant=participant,
    )


def toggle_participant_checkin(participant: Participant, *, new_value: bool) -> RegistrationOpResult:
    event = participant.registration.event

    if not participant.is_paid and event.price > 0:
        raise ParticipantCheckinNotAllowed("Não é possível fazer check-in sem pagamento confirmado")

    with transaction.atomic():
        participant.mark_checked_in(new_value)
        participant.save(update_fields=["checked_in", "checked_in_at"])

    return RegistrationOpResult(
        event=event,
        registration=participant.registration,
        participant=participant,
    )


def checkin_all(registration: Registration) -> RegistrationOpResult:
    event = registration.event

    if event.price > 0 and registration.participants.filter(is_paid=False).exists():
        raise BulkCheckinNotAllowed("Ainda existem participantes por pagar")

    now = timezone.now()

    with transaction.atomic():
        for participant in registration.participants.all():
            if not participant.checked_in:
                participant.checked_in = True
                participant.checked_in_at = now
                participant.save(update_fields=["checked_in", "checked_in_at"])

    return RegistrationOpResult(event=event, registration=registration)