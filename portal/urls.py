from django.urls import path

from . import views

urlpatterns = [
    path("p/<int:tenant_id>/<int:site_id>", views.splash, name="portal-splash"),
    path("p/<int:tenant_id>/<int:site_id>/ads", views.ad_decision, name="portal-ads"),
    path("e", views.event_ingest, name="portal-event"),
    # Auth
    path("auth/clickthrough", views.auth_clickthrough, name="auth-clickthrough"),
    path("auth/email-otp", views.auth_email_otp, name="auth-email-otp"),
    path("auth/email-otp/verify", views.auth_email_otp_verify, name="auth-email-otp-verify"),
    path("auth/voucher", views.auth_voucher, name="auth-voucher"),
    # Ruckus WISPr
    path("ruckus/wispr/login", views.ruckus_wispr_login, name="ruckus-wispr-login"),
    path("ruckus/coa", views.ruckus_coa_stub, name="ruckus-coa"),
]
