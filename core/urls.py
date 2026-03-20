from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("sobre/", views.about, name="about"),
    path("ministerios/", views.ministerios, name="ministerios"),
    path("contactos/", views.contacts, name="contacts"),

    
]
