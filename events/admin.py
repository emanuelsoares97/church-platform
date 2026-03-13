from django.contrib import admin
from .models import Event, Registration, Participant


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "location", "price", "is_active", "banner_status")
    list_filter = ("is_active", "date")
    search_fields = ("title", "location")
    prepopulated_fields = {"slug": ("title",)}

    def banner_status(self, obj):
        return "Sim" if obj.banner_image else "Não"

    banner_status.short_description = "Banner"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("buyer_name", "event", "ticket_qty", "payment_method", "is_paid", "created_at")
    list_filter = ("event", "payment_method", "is_paid", "created_at")
    search_fields = ("buyer_name", "buyer_email", "phone")
    ordering = ("-created_at",)
    inlines = [ParticipantInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        current = obj.participants.count()
        missing = obj.ticket_qty - current
        if missing > 0:
            Participant.objects.bulk_create(
                [Participant(registration=obj, full_name="") for _ in range(missing)]
            )

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "registration", "checked_in")
    list_filter = ("checked_in", "registration__event")
    search_fields = ("full_name",)