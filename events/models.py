from decimal import Decimal
import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    date = models.DateField()
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("5.00"))
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to="events/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
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
        return self.title


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

    # compat (inscrição toda paga)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    # valor total pago nesta inscrição (pode ser parcial)
    paid_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_paid(self, value: bool):
        # marca a inscrição como paga (total)
        self.is_paid = value
        self.paid_at = timezone.now() if value else None

    @property
    def total_price(self):
        return self.ticket_qty * self.event.price

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.total_price

    def __str__(self):
        return f"{self.buyer_name} • {self.event.title}"


class Participant(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    full_name = models.CharField(max_length=200, blank=True)

    # código do bilhete (único)
    ticket_code = models.CharField(max_length=32, unique=True, db_index=True)

    # pagamento do participante
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    # check-in do participante
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(blank=True, null=True)

    def mark_paid(self, value: bool):
        self.is_paid = value
        self.paid_at = timezone.now() if value else None

    def mark_checked_in(self, value: bool):
        self.checked_in = value
        self.checked_in_at = timezone.now() if value else None

    def __str__(self):
        return self.full_name