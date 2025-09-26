from django.urls import path

from . import views

urlpatterns = [
    path("p/<int:tenant_id>/<int:site_id>", views.splash, name="portal-splash"),
    path("p/<int:tenant_id>/<int:site_id>/ads", views.ad_decision, name="portal-ads"),
    path("e", views.event_ingest, name="portal-event"),
]
