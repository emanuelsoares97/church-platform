from __future__ import annotations

import requests
from django.conf import settings
from django.template.loader import render_to_string

from events.models import Registration


# envia o email através da api do resend
def _send_email_resend(subject: str, html: str, to_email: str) -> None:
    if not settings.RESEND_API_KEY:
        raise ValueError("RESEND_API_KEY não está configurada.")

    url = "https://api.resend.com/emails"

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "church-platform/1.0",
    }

    payload = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20,
    )

    if not response.ok:
        try:
            error_data = response.json()
        except ValueError:
            error_data = response.text

        raise RuntimeError(
            f"Erro ao enviar email com Resend. "
            f"Status: {response.status_code}. "
            f"Resposta: {error_data}"
        )


# envia os bilhetes da inscrição
def send_registration_tickets_email(registration_id: int) -> None:
    reg = (
        Registration.objects
        .select_related("event")
        .prefetch_related("participants")
        .get(id=registration_id)
    )

    manage_url = f"{settings.SITE_URL}/evento/{reg.event.slug}/sucesso/{reg.public_id}/"

    participants = list(reg.participants.all())
    if not participants:
        return

    for participant in participants:
        participant_name = participant.full_name
        ticket_code = participant.ticket_code
        to_email = reg.buyer_email

        subject = f"Bilhete — {reg.event.title} — {participant_name}"
        qr_image_url = f"{settings.SITE_URL}/ticket/{ticket_code}/qr.png"

        context = {
            "reg": reg,
            "event": reg.event,
            "manage_url": manage_url,
            "site_name": "Church Platform",
            "participant_name": participant_name,
            "ticket_code": ticket_code,
            "qr_image_url": qr_image_url,
        }

        html = render_to_string("emails/registration_ticket.html", context)

        _send_email_resend(
            subject=subject,
            html=html,
            to_email=to_email,
        )
