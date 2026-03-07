from __future__ import annotations

from email.mime.image import MIMEImage
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from events.models import Registration


def _attach_inline_png(msg: EmailMultiAlternatives, png_bytes: bytes, cid: str, filename: str) -> None:
    image = MIMEImage(png_bytes, _subtype="png")
    image.add_header("Content-ID", f"<{cid}>")
    image.add_header("Content-Disposition", "inline", filename=filename)
    msg.attach(image)


def _attach_inline_file_image(msg: EmailMultiAlternatives, file_path: str, cid: str, filename: str) -> None:
    with open(file_path, "rb") as f:
        data = f.read()
    image = MIMEImage(data)
    image.add_header("Content-ID", f"<{cid}>")
    image.add_header("Content-Disposition", "inline", filename=filename)
    msg.attach(image)


def _make_qr_png(data: str, box_size: int = 6, border: int = 2) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


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

    has_banner = bool(getattr(reg.event, "banner_image", None))
    banner_path = None
    if has_banner and reg.event.banner_image:
        try:
            banner_path = reg.event.banner_image.path
        except Exception:
            banner_path = None
            has_banner = False

    for p in participants:
        participant_name = p.full_name
        ticket_code = p.ticket_code

        subject = f"Bilhete — {reg.event.title} — {participant_name}"
        to_email = reg.buyer_email

        # direciona atraves do qr code para o participante
        qr_target = f"{settings.SITE_URL}/gestao/t/{ticket_code}/"

        context = {
            "reg": reg,
            "event": reg.event,
            "manage_url": manage_url,
            "site_name": "SNT Almada",
            "participant_name": participant_name,
            "ticket_code": ticket_code,
            "has_banner": has_banner,
        }

        html = render_to_string("emails/registration_ticket.html", context)
        text = strip_tags(html)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html, "text/html")

        qr_png = _make_qr_png(qr_target)
        _attach_inline_png(msg, qr_png, cid="qr_img", filename=f"qr-{ticket_code}.png")

        if banner_path:
            _attach_inline_file_image(msg, banner_path, cid="banner_img", filename="banner.png")

        msg.send()