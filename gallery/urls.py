from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.album_list, name="album_list"),
    path("criar/", views.create_album, name="create_album"),
    path("<slug:slug>/", views.album_detail, name="album_detail"),
    path("<slug:slug>/editar/", views.edit_album, name="edit_album"),
    path("image/<int:image_id>/delete/", views.delete_image, name="delete_image"),
    path("<slug:slug>/delete-selected/", views.delete_selected_images, name="delete_selected_images"),
]