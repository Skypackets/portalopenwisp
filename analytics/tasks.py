from __future__ import annotations

from datetime import date

from django.db import models
from django.db.models import Count

from ads.models import Event

from .models import DailyAggregate


def recompute_daily_for(date_value: date) -> None:
    # Compute impressions, clicks, sessions grouped by tenant, site
    base = Event.objects.filter(ts__date=date_value)
    grouped = (
        base.values("tenant_id", "site_id")
        .annotate(
            impressions=Count("id", filter=models.Q(type="impression")),
            clicks=Count("id", filter=models.Q(type="click")),
            sessions=Count("id", filter=models.Q(type="session_start")),
        )
        .iterator()
    )
    for row in grouped:
        agg, _ = DailyAggregate.objects.get_or_create(
            date=date_value,
            tenant_id=row["tenant_id"],
            site_id=row["site_id"],
            defaults={"impressions": 0, "clicks": 0, "sessions": 0},
        )
        agg.impressions = row["impressions"]
        agg.clicks = row["clicks"]
        agg.sessions = row["sessions"]
        agg.save()
