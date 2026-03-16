from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.album_list, name="album_list"),
    path("<slug:slug>/", views.album_detail, name="album_detail"),
]