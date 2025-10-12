from django.db import models
from django.utils import timezone

from core.models import Brand, Site, Tenant


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Page(TimeStampedModel):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="pages")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="pages")
    site = models.ForeignKey(
        Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="pages"
    )
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="draft")
    html = models.TextField(blank=True, default="")
    css = models.TextField(blank=True, default="")
    js = models.TextField(blank=True, default="")
    rev = models.CharField(max_length=64, default="v1")
    publish_at = models.DateTimeField(null=True, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)
    blocks_json = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.name}:{self.rev}"


class PageRevision(TimeStampedModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="revisions")
    rev = models.CharField(max_length=64)
    html = models.TextField(blank=True, default="")
    css = models.TextField(blank=True, default="")
    js = models.TextField(blank=True, default="")
    blocks_json = models.JSONField(default=list, blank=True)


# Create your models here.
