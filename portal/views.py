from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ads.models import Campaign, Creative, Event, Slot
from contentmgmt.models import Page
from core.models import Site, Tenant


@require_GET
def splash(request: HttpRequest, tenant_id: int, site_id: int) -> HttpResponse:
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        site = Site.objects.get(id=site_id, tenant=tenant)
    except (Tenant.DoesNotExist, Site.DoesNotExist) as exc:
        raise Http404 from exc

    page = (
        Page.objects.filter(tenant=tenant, site=site, status="published")
        .order_by("-updated_at")
        .first()
    )
    if page is None:
        raise Http404("No published page")

    # basic event record
    Event.objects.create(tenant=tenant, site=site, type="splash_view", payload_json={})

    # Render stored HTML if present; otherwise fallback to template
    if page.html:
        return HttpResponse(page.html)
    return render(request, "home.html", {"app_name": "Portal OpenWISP"})


@require_GET
def ad_decision(request: HttpRequest, tenant_id: int, site_id: int) -> JsonResponse:
    slot = request.GET.get("slot")
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        site = Site.objects.get(id=site_id, tenant=tenant)
    except (Tenant.DoesNotExist, Site.DoesNotExist) as exc:
        raise Http404 from exc

    # Very simple selector: pick most recent creative from any active campaign
    campaign = (
        Campaign.objects.filter(tenant=tenant, status="active").order_by("-updated_at").first()
    )
    creative = None
    if campaign is not None:
        creative = campaign.creatives.order_by("-updated_at").first()

    payload = {"creative": None}
    if creative is not None:
        payload["creative"] = {
            "type": creative.type,
            "asset_url": creative.asset_url,
            "click_url": creative.click_url,
            "width": creative.width,
            "height": creative.height,
            "slot": slot,
        }
        Event.objects.create(
            tenant=tenant,
            site=site,
            type="impression",
            payload_json={"slot": slot, "creative_id": creative.id, "campaign_id": campaign.id},
        )
    return JsonResponse(payload)


@require_POST
def event_ingest(request: HttpRequest) -> JsonResponse:
    # In MVP, accept basic JSON without auth; production should require signed tokens
    data = request.POST or {}
    Event.objects.create(
        tenant_id=data.get("tenant_id"),
        site_id=data.get("site_id"),
        type=data.get("type", "click"),
        payload_json=data,
    )
    return JsonResponse({"ok": True})


from django.shortcuts import render

# Create your views here.
