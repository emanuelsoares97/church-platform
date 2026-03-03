from django.urls import path, include
from . import views

app_name = "events"

urlpatterns = [
    path("eventos/", views.event_list, name="event_list"),
    path("evento/<slug:slug>/", views.event_detail, name="event_detail"),
    path(
    "evento/<slug:slug>/sucesso/<uuid:public_id>/",
    views.registration_success,
    name="registration_success",
),
    
]