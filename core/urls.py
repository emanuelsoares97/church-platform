from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("sobre/", views.about, name="about"),
    path("ministerios/", views.ministerios, name="ministerios"),
    path("ministerios/kids/", views.ministry_kids, name="ministry_kids"),
    path("ministerios/jovens/", views.ministry_young, name="ministry_young"),
    path("contactos/", views.contacts, name="contacts"),
]
