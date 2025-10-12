from __future__ import annotations

from django.db import models


class DailyAggregate(models.Model):
    date = models.DateField()
    tenant_id = models.IntegerField()
    site_id = models.IntegerField()
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    sessions = models.IntegerField(default=0)

    class Meta:
        unique_together = ("date", "tenant_id", "site_id")
        indexes = [
            models.Index(fields=["tenant_id", "site_id", "date"], name="agg_tsd_idx"),
        ]
