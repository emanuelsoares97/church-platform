from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.conf import settings


def manifest(request):
    data = render_to_string("pwa/manifest.json")
    return HttpResponse(data, content_type="application/manifest+json")


def service_worker(request):
    data = render_to_string("pwa/sw.js", {
        "APP_VERSION": settings.APP_VERSION
    })
    response = HttpResponse(data, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "pwa/offline.html")