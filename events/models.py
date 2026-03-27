from decimal import Decimal
import uuid

from cloudinary.models import CloudinaryField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    date = models.DateField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("5.00"))
    description = models.TextField(blank=True)
    banner_image = CloudinaryField(
        "event_banner",
        blank=True,
        null=True,
        folder="church-platform/events",
    )
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 2
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or "Evento sem título"

    def is_past(self):
        """Verifica se a data do evento já passou."""
        return timezone.now().date() > self.date

    def is_registration_open(self):
        """Indica se o evento ainda aceita novas inscrições."""
        if not self.registration_deadline:
            return True
        return timezone.now() <= self.registration_deadline

    def can_accept_registrations(self):
        """
        Verifica se o evento pode aceitar novas inscrições.
        Requer: estar ativo, não arquivado, prazo aberto, data ainda não passou.
        """
        return (
            self.is_active
            and not self.is_archived
            and self.is_registration_open()
            and not self.is_past()
        )


class Registration(models.Model):
    class PaymentMethod(models.TextChoices):
        MBWAY = "MBWAY", "MB Way"
        LOCAL = "LOCAL", "Pagamento no local"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")

    buyer_name = models.CharField(max_length=200)
    buyer_email = models.EmailField()
    phone = models.CharField(max_length=20)

    ticket_qty = models.PositiveIntegerField(default=1)

    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MBWAY,
    )

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    paid_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_paid(self, value: bool):
        self.is_paid = value
        self.paid_at = timezone.now() if value else None

    @property
    def total_price(self):
        return self.ticket_qty * self.event.price

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.total_price

    def __str__(self):
        buyer = self.buyer_name or "Sem comprador"
        event_title = self.event.title if self.event and self.event.title else "Sem evento"
        return f"{buyer} • {event_title}"

class Participant(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    full_name = models.CharField(max_length=120, blank=True)
    ticket_code = models.CharField(max_length=50, unique=True, blank=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(blank=True, null=True)

    def mark_checked_in(self, value: bool):
        self.checked_in = value
        if value:
            self.checked_in_at = timezone.now()
        else:
            self.checked_in_at = None
        self.save(update_fields=["checked_in", "checked_in_at"])

    def mark_paid(self, value: bool):
        self.is_paid = value
        self.paid_at = timezone.now() if value else None
        self.save(update_fields=["is_paid", "paid_at"])

    def __str__(self):
        return self.full_name or f"Participante #{self.pk or 'novo'}"