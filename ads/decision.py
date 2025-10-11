from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from django.core.cache import cache
from django.conf import settings

from .models import Campaign, Creative


@dataclass
class Decision:
    creative: Optional[Creative]
    reason: str = ""


def _cache_key(prefix: str, tenant_id: int, site_id: int, mac: str, slot: str) -> str:
    mac_norm = (mac or "").lower()
    digest = hashlib.sha256(f"{tenant_id}:{site_id}:{mac_norm}:{slot}".encode()).hexdigest()[:16]
    return f"ads:{prefix}:{digest}"


def _within_schedule(campaign: Campaign, now: datetime) -> bool:
    if campaign.start_at and now < campaign.start_at:
        return False
    if campaign.end_at and now > campaign.end_at:
        return False
    return campaign.status == "active"


def decide_ad(tenant_id: int, site_id: int, slot: str, mac: str = "") -> Decision:
    now = datetime.now(timezone.utc)
    # Simple targeting: latest active, scheduled campaign with a creative
    qs = Campaign.objects.filter(tenant_id=tenant_id, status="active").order_by("-updated_at")
    for campaign in qs:
        if not _within_schedule(campaign, now):
            continue
        creative = campaign.creatives.order_by("-updated_at").first()
        if not creative:
            continue
        # Frequency capping per device+slot
        if mac:
            cap_key = _cache_key("cap", tenant_id, site_id, mac, slot)
            count = cache.get(cap_key, 0)
            cap_limit = getattr(settings, "ADS_FREQ_CAP_PER_HOUR", 3)
            if count >= cap_limit:
                return Decision(None, reason="freq_capped")
        # Pacing: naive throttle via cache token per slot
        pace_key = f"ads:pace:t{tenant_id}:s{site_id}:{slot}"
        pace_seconds = getattr(settings, "ADS_PACING_SECONDS", 10)
        if pace_seconds > 0:
            if cache.get(pace_key):
                return Decision(None, reason="paced")
            cache.set(pace_key, 1, timeout=pace_seconds)
        return Decision(creative, reason="ok")
    return Decision(None, reason="no_active_campaign")


def record_impression_for_mac(tenant_id: int, site_id: int, slot: str, mac: str = "") -> None:
    if not mac:
        return
    cap_key = _cache_key("cap", tenant_id, site_id, mac, slot)
    count = cache.get(cap_key, 0)
    cache.set(cap_key, count + 1, timeout=3600)
