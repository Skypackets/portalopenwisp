from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import render


def healthcheck(_request):
    return HttpResponse("ok")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthcheck),
    path("", lambda r: render(r, "index.html")),
]

