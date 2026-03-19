from django.urls import path
from . import views

app_name = "management"

urlpatterns = [
    path("", views.dashboard, name="home"),
    path("eventos/", views.events_list, name="events_list"),
    path("evento/<int:event_id>/inscricoes/", views.event_registrations, name="event_regs"),

    # pagamentos / check-in
    path("inscricao/<int:reg_id>/mark-paid-full/", views.mark_registration_paid_full, name="mark_registration_paid_full"),
    path("participante/<int:participant_id>/toggle-paid/", views.toggle_participant_paid, name="toggle_participant_paid"),
    path("participante/<int:participant_id>/toggle-checkin/", views.toggle_participant_checkin, name="toggle_participant_checkin"),
    path("inscricao/<int:reg_id>/checkin-all/", views.checkin_all, name="checkin_all"),

    # scan qr
    path("scan/", views.scan_page, name="scan"),

    # API usada pelo scanner para validar e fazer check-in automático
    path("scan/checkin-api/", views.scan_checkin_api, name="scan_checkin_api"),

    path("t/<str:ticket_code>/", views.ticket_lookup, name="ticket_lookup"),
    path("inscricao/<int:reg_id>/grupo/", views.registration_group, name="registration_group"),

    path(
        "eventos/<int:event_id>/export/excel/",
        views.export_event_registrations_excel,
        name="export_event_registrations_excel",
    ),
]