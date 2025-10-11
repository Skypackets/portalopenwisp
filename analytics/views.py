from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Sum
from rest_framework import decorators, response, status

from ads.models import Event
from .models import DailyAggregate


@decorators.api_view(["GET"])
def daily_summary(request):
    tenant_id = request.query_params.get("tenant_id")
    site_id = request.query_params.get("site_id")
    days = int(request.query_params.get("days", 7))
    qs = DailyAggregate.objects.all()
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if site_id:
        qs = qs.filter(site_id=site_id)
    start = date.today() - timedelta(days=days - 1)
    qs = qs.filter(date__gte=start).order_by("date")
    data = [
        {
            "date": str(row.date),
            "tenant_id": row.tenant_id,
            "site_id": row.site_id,
            "impressions": row.impressions,
            "clicks": row.clicks,
            "sessions": row.sessions,
        }
        for row in qs
    ]
    return response.Response(data, status=status.HTTP_200_OK)
