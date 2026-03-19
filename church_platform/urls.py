from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views_pwa import manifest, service_worker, offline

urlpatterns = [
    path("admin/", admin.site.urls),

    # login / logout
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # site público
    path("", include("events.urls")),

    # gestão
    path("gestao/", include(("events.management_urls", "events_mgmt"), namespace="events_mgmt")),
    
    #paginas principais
    path("", include("core.urls")),

    #galeria
    path("galeria/", include("gallery.urls")),

    #pwa
    path("manifest.json", manifest, name="manifest"),
    path("sw.js", service_worker, name="service_worker"),
    path("offline/", offline, name="offline"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)