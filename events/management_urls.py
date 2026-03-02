from django.urls import path
from . import management_views as mv

app_name = "events_mgmt"

urlpatterns = [
    path("", mv.dashboard_home, name="home"),
    path("evento/<int:event_id>/inscricoes/", mv.event_registrations, name="event_regs"),
    path("inscricao/<int:reg_id>/toggle-paid/", mv.toggle_paid, name="toggle_paid"),
    path("participante/<int:participant_id>/toggle-checkin/", mv.toggle_participant_checkin, name="toggle_participant_checkin"),
]