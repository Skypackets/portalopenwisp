from django.db import models
from django.utils import timezone

from core.models import Site, Tenant


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GuestUser(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="guest_users")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    social_id = models.CharField(max_length=128, blank=True, default="")
    mac = models.CharField(max_length=17)
    mac_hash = models.CharField(max_length=64, blank=True, default="")
    consent_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.mac}"


class Voucher(TimeStampedModel):
    STATUS_CHOICES = (("active", "Active"), ("used", "Used"), ("inactive", "Inactive"))
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="vouchers")
    code = models.CharField(max_length=64, unique=True)
    policy_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    used_by_mac = models.CharField(max_length=17, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)


class Session(TimeStampedModel):
    user = models.ForeignKey(GuestUser, on_delete=models.CASCADE, related_name="sessions")
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="sessions")
    mac = models.CharField(max_length=17)
    ip = models.GenericIPAddressField(null=True, blank=True)
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)
    bytes_up = models.BigIntegerField(default=0)
    bytes_down = models.BigIntegerField(default=0)
    policy_json = models.JSONField(default=dict, blank=True)


class EmailOTP(TimeStampedModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    email = models.EmailField()
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)


# Create your models here.
