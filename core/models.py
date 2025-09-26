from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=32, default="active")
    plan = models.CharField(max_length=64, blank=True, default="")
    settings_json = models.JSONField(default=dict, blank=True)
    secret_salt = models.CharField(max_length=64, blank=True, default="")

    def __str__(self) -> str:
        return self.name


class Brand(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=200)
    theme_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.name}"


class Site(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sites")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="sites")
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True, default="")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.name}"


class Controller(TimeStampedModel):
    TYPE_CHOICES = (
        ("ruckus_sz", "Ruckus SmartZone/vSZ"),
        ("cambium_cnmaestro", "Cambium cnMaestro"),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="controllers")
    type = models.CharField(max_length=64, choices=TYPE_CHOICES)
    base_url = models.URLField()
    api_key = models.CharField(max_length=256, blank=True, default="")
    api_secret = models.CharField(max_length=256, blank=True, default="")
    radius_profile_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.type}"


class SSID(TimeStampedModel):
    AUTH_MODE_CHOICES = (
        ("clickthrough", "Click-through"),
        ("email_otp", "Email OTP"),
        ("voucher", "Voucher"),
        ("radius", "RADIUS Username/Password"),
    )
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="ssids")
    name = models.CharField(max_length=128)
    auth_mode = models.CharField(max_length=32, choices=AUTH_MODE_CHOICES, default="clickthrough")
    controller = models.ForeignKey(Controller, on_delete=models.PROTECT, related_name="ssids")
    walled_garden_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.site_id}:{self.name}"


# Create your models here.
