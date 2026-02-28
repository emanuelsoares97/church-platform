from django.db import models
from django.utils.text import slugify


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    date = models.DateField()
    location = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to="events/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Registration(models.Model):

    class PaymentMethod(models.TextChoices):
        MBWAY = "MBWAY", "MB Way"
        LOCAL = "LOCAL", "Pagamento no local"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    buyer_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    ticket_qty = models.PositiveIntegerField(default=1)
    payment_method = models.CharField(
    max_length=10,
    choices=PaymentMethod.choices,
    default=PaymentMethod.MBWAY
)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.ticket_qty * self.event.price

    def __str__(self):
        return f"{self.buyer_name} • {self.event.title}"


class Participant(models.Model):
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    full_name = models.CharField(max_length=200, blank=True)
    checked_in = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name