from django.db import models
from django.utils import timezone

from contentmgmt.models import Page
from core.models import Site, Tenant


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Campaign(TimeStampedModel):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="active")
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    targeting_json = models.JSONField(default=dict, blank=True)
    pacing_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.name}"


class Creative(TimeStampedModel):
    TYPE_CHOICES = (
        ("image", "Image"),
        ("video", "Video"),
        ("html", "HTML5"),
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="creatives")
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    asset_url = models.URLField()
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    click_url = models.URLField()
    meta_json = models.JSONField(default=dict, blank=True)


class Slot(TimeStampedModel):
    POSITION_CHOICES = (
        ("hero", "Hero"),
        ("banner", "Banner"),
    )
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="slots")
    position = models.CharField(max_length=32, choices=POSITION_CHOICES)
    sizes = models.CharField(max_length=64, default="")
    rules_json = models.JSONField(default=dict, blank=True)


class Event(TimeStampedModel):
    TYPE_CHOICES = (
        ("impression", "Impression"),
        ("click", "Click"),
        ("splash_view", "Splash View"),
    )
    ts = models.DateTimeField(default=timezone.now)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    payload_json = models.JSONField(default=dict, blank=True)


# Create your models here.
