import random
import string

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from ads.models import Campaign, Creative, Event, Slot
from authsvc.models import EmailOTP, GuestUser, Session, Voucher
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


# --- Auth Endpoints (MVP) ---


@require_POST
def auth_clickthrough(request: HttpRequest) -> JsonResponse:
    tenant_id = int(request.POST.get("tenant_id"))
    site_id = int(request.POST.get("site_id"))
    mac = request.POST.get("mac", "00:00:00:00:00:00")
    tenant = Tenant.objects.get(id=tenant_id)
    site = Site.objects.get(id=site_id, tenant=tenant)

    user, _ = GuestUser.objects.get_or_create(tenant=tenant, mac=mac)
    session = Session.objects.create(
        user=user, site=site, mac=mac, policy_json={"type": "clickthrough"}
    )
    return JsonResponse({"ok": True, "session_id": session.id})


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


@require_POST
def auth_email_otp(request: HttpRequest) -> JsonResponse:
    tenant_id = int(request.POST.get("tenant_id"))
    email = request.POST.get("email")
    code = _generate_code()
    expires = timezone.now() + timezone.timedelta(minutes=10)
    otp = EmailOTP.objects.create(tenant_id=tenant_id, email=email, code=code, expires_at=expires)
    # In production, send email via provider. For MVP/dev, return the code to caller for verification.
    return JsonResponse({"ok": True, "otp_id": otp.id, "dev_code": code})


@require_POST
def auth_email_otp_verify(request: HttpRequest) -> JsonResponse:
    tenant_id = int(request.POST.get("tenant_id"))
    site_id = int(request.POST.get("site_id"))
    mac = request.POST.get("mac", "00:00:00:00:00:00")
    email = request.POST.get("email")
    code = request.POST.get("code")
    tenant = Tenant.objects.get(id=tenant_id)
    site = Site.objects.get(id=site_id, tenant=tenant)

    otp = (
        EmailOTP.objects.filter(tenant=tenant, email=email, code=code)
        .order_by("-created_at")
        .first()
    )
    if otp is None or otp.expires_at < timezone.now():
        return JsonResponse({"ok": False, "error": "invalid_or_expired"}, status=400)
    otp.verified_at = timezone.now()
    otp.save(update_fields=["verified_at"])

    user, _ = GuestUser.objects.get_or_create(tenant=tenant, mac=mac, defaults={"email": email})
    if not user.email:
        user.email = email
        user.save(update_fields=["email"])
    session = Session.objects.create(
        user=user, site=site, mac=mac, policy_json={"type": "email_otp"}
    )
    return JsonResponse({"ok": True, "session_id": session.id})


@require_POST
def auth_voucher(request: HttpRequest) -> JsonResponse:
    tenant_id = int(request.POST.get("tenant_id"))
    site_id = int(request.POST.get("site_id"))
    mac = request.POST.get("mac", "00:00:00:00:00:00")
    code = request.POST.get("code")
    tenant = Tenant.objects.get(id=tenant_id)
    site = Site.objects.get(id=site_id, tenant=tenant)

    try:
        voucher = Voucher.objects.get(tenant=tenant, code=code, status="active")
    except Voucher.DoesNotExist:
        return JsonResponse({"ok": False, "error": "invalid_voucher"}, status=400)

    user, _ = GuestUser.objects.get_or_create(tenant=tenant, mac=mac)
    session = Session.objects.create(user=user, site=site, mac=mac, policy_json={"type": "voucher"})

    # Mark single-use (basic behavior)
    voucher.status = "used"
    voucher.used_by_mac = mac
    voucher.used_at = timezone.now()
    voucher.save(update_fields=["status", "used_by_mac", "used_at"])
    return JsonResponse({"ok": True, "session_id": session.id})


# --- Ruckus WISPr (MVP stub) ---


@require_POST
def ruckus_wispr_login(request: HttpRequest) -> HttpResponse:
    # Accepts Ruckus WISPr login form post. MVP: always success and return minimal response.
    # In production, validate credentials or session token and authorize on controller.
    response_xml = """<?xml version='1.0'?>
<WISPAccessGatewayParam>
  <ProxyResponse>
    <MessageType>120</MessageType>
    <ResponseCode>50</ResponseCode>
    <ReplyMessage>Login Succeeded</ReplyMessage>
  </ProxyResponse>
</WISPAccessGatewayParam>"""
    return HttpResponse(response_xml, content_type="application/xml")


@require_POST
def ruckus_coa_stub(request: HttpRequest) -> JsonResponse:
    # Placeholder for Change-of-Authorization: in MVP, just acknowledge request
    return JsonResponse({"ok": True, "message": "CoA sent (stub)"})
