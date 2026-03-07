from django.urls import path
from . import management_views as mv

app_name = "events_mgmt"

urlpatterns = [
    path("", mv.dashboard_home, name="home"),
    path("evento/<int:event_id>/inscricoes/", mv.event_registrations, name="event_regs"),

    # pagamentos / check-in
    path("inscricao/<int:reg_id>/mark-paid-full/", mv.mark_registration_paid_full, name="mark_registration_paid_full"),
    path("participante/<int:participant_id>/toggle-paid/", mv.toggle_participant_paid, name="toggle_participant_paid"),
    path("participante/<int:participant_id>/toggle-checkin/", mv.toggle_participant_checkin, name="toggle_participant_checkin"),
    path("inscricao/<int:reg_id>/checkin-all/", mv.checkin_all, name="checkin_all"),

    # scan qr
    path("scan/", mv.scan_page, name="scan"),

    # API usada pelo scanner para validar e fazer check-in automatico
    path("scan/checkin-api/", mv.scan_checkin_api, name="scan_checkin_api"),

    path("t/<str:ticket_code>/", mv.ticket_lookup, name="ticket_lookup"),
    path("inscricao/<int:reg_id>/grupo/", mv.registration_group, name="registration_group"),
]