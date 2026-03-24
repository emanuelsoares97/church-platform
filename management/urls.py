from django.urls import path
from . import views

app_name = "management"

urlpatterns = [
    path("", views.dashboard, name="home"),
    path("eventos/gestao/", views.events_hub, name="events_hub"),
    path("galeria/gestao/", views.gallery_hub, name="gallery_hub"),
    path("galeria/albuns/", views.gallery_albums_list, name="gallery_albums_list"),
    path("galeria/albuns/<slug:slug>/", views.management_album_detail, name="management_album_detail"),
    path("eventos/", views.events_list, name="events_list"),
    path("eventos/administracao/", views.events_admin_list, name="events_admin_list"),
    path("eventos/criar/", views.create_event_view, name="create_event"),
    path("eventos/<int:event_id>/editar/", views.edit_event_view, name="event_edit"),
    path("eventos/<int:event_id>/ativar/", views.activate_event, name="event_activate"),
    path("eventos/<int:event_id>/desativar/", views.deactivate_event, name="event_deactivate"),
    path("eventos/<int:event_id>/arquivar/", views.archive_event, name="event_archive"),
    path("eventos/<int:event_id>/desarquivar/", views.unarchive_event, name="event_unarchive"),

    path("evento/<int:event_id>/inscricoes/", views.event_registrations, name="event_regs"),

    path("inscricao/<int:reg_id>/mark-paid-full/", views.mark_registration_paid_full, name="mark_registration_paid_full"),
    path("participante/<int:participant_id>/toggle-paid/", views.toggle_participant_paid, name="toggle_participant_paid"),
    path("participante/<int:participant_id>/toggle-checkin/", views.toggle_participant_checkin, name="toggle_participant_checkin"),
    path("inscricao/<int:reg_id>/checkin-all/", views.checkin_all, name="checkin_all"),

    path("scan/", views.scan_page, name="scan"),
    path("scan/checkin-api/", views.scan_checkin_api, name="scan_checkin_api"),

    path("t/<str:ticket_code>/", views.ticket_lookup, name="ticket_lookup"),
    path("inscricao/<int:reg_id>/grupo/", views.registration_group, name="registration_group"),

    path(
        "eventos/<int:event_id>/export/excel/",
        views.export_event_registrations_excel,
        name="export_event_registrations_excel",
    ),
    path("relatorios/", views.reports, name="reports"),
    path("eventos/<int:event_id>/relatorio/", views.event_report, name="event_report"),
]