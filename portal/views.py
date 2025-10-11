import hashlib
import hmac
import random
import string
import urllib.parse

import bleach
from django.conf import settings
from django.core.cache import cache
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from ads.models import Campaign, Event
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

    Event.objects.create(tenant=tenant, site=site, type="splash_view", payload_json={})

    if page.html:
        allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS) | {"img", "video", "source", "link", "meta"}
        sanitized = bleach.clean(
            page.html,
            tags=allowed_tags,
            attributes={
                "*": [
                    "class",
                    "style",
                    "id",
                    "href",
                    "src",
                    "width",
                    "height",
                    "type",
                    "rel",
                ]
            },
            protocols=["http", "https", "data"],
        )
        resp = HttpResponse(sanitized)
        resp["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https: data:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https:; "
            "frame-src 'self' https:;"
        )
        return resp
    hero_zone_slug = f"t{tenant.id}-s{site.id}-hero"
    return render(
        request,
        "home.html",
        {
            "app_name": "Sky Packets Portal",
            "hero_zone_slug": hero_zone_slug,
            "tenant_id": tenant.id,
            "site_id": site.id,
        },
    )


@require_GET
def ad_decision(request: HttpRequest, tenant_id: int, site_id: int) -> JsonResponse:
    slot = request.GET.get("slot")
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        site = Site.objects.get(id=site_id, tenant=tenant)
    except (Tenant.DoesNotExist, Site.DoesNotExist) as exc:
        raise Http404 from exc

    campaign = (
        Campaign.objects.filter(tenant=tenant, status="active").order_by("-updated_at").first()
    )
    creative = campaign.creatives.order_by("-updated_at").first() if campaign else None

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
        # Provide a first-party tracking redirect URL
        try:
            encoded_target = urllib.parse.quote(creative.click_url, safe="")
            tracking_qs = urllib.parse.urlencode(
                {
                    "tenant_id": tenant.id,
                    "site_id": site.id,
                    "slot": slot or "",
                    "creative_id": creative.id,
                    "u": creative.click_url,
                }
            )
            payload["creative"]["tracking_url"] = f"/r?{tracking_qs}"
        except Exception:
            # do not block rendering on encoding issues
            pass
        Event.objects.create(
            tenant=tenant,
            site=site,
            type="impression",
            payload_json={
                "slot": slot,
                "creative_id": creative.id,
                "campaign_id": campaign.id,
            },
        )
    return JsonResponse(payload)


@require_POST
def event_ingest(request: HttpRequest) -> JsonResponse:
    data = request.POST or {}
    tenant_id = data.get("tenant_id")
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return JsonResponse({"ok": False, "error": "tenant"}, status=400)
    signature = request.headers.get("X-Portal-Signature", "")
    body = request.body or b""
    secret = (tenant.secret_salt or "").encode("utf-8")
    computed = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not settings.ALLOW_UNAUTH_EVENTS and signature != f"sha256={computed}":
        return JsonResponse({"ok": False, "error": "sig"}, status=401)
    Event.objects.create(
        tenant_id=tenant_id,
        site_id=data.get("site_id"),
        type=data.get("type", "click"),
        payload_json=data,
    )
    return JsonResponse({"ok": True})


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
    rl_key = f"otp:{tenant_id}:{email}"
    if cache.get(rl_key):
        return JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
    cache.set(rl_key, 1, timeout=60)
    otp = EmailOTP.objects.create(tenant_id=tenant_id, email=email, code=code, expires_at=expires)
    payload = {"ok": True, "otp_id": otp.id}
    if settings.DEBUG:
        payload["dev_code"] = code
    return JsonResponse(payload)


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

    from django.db import transaction
    try:
        with transaction.atomic():
            voucher = (
                Voucher.objects.select_for_update()
                .get(tenant=tenant, code=code, status="active")
            )
            # mark redeemed within the transaction
            voucher.status = "used"
            voucher.used_by_mac = mac
            voucher.used_at = timezone.now()
            voucher.save(update_fields=["status", "used_by_mac", "used_at"])
    except Voucher.DoesNotExist:
        return JsonResponse({"ok": False, "error": "invalid_voucher"}, status=400)

    user, _ = GuestUser.objects.get_or_create(tenant=tenant, mac=mac)
    session = Session.objects.create(user=user, site=site, mac=mac, policy_json={"type": "voucher"})

    return JsonResponse({"ok": True, "session_id": session.id})


@require_POST
def ruckus_wispr_login(request: HttpRequest) -> HttpResponse:
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
    return JsonResponse({"ok": True, "message": "CoA sent (stub)"})


@require_GET
def redirect_click(request: HttpRequest) -> HttpResponse:
    """First-party click redirect that logs a click event then redirects."""
    target = request.GET.get("u", "")
    tenant_id = request.GET.get("tenant_id")
    site_id = request.GET.get("site_id")
    creative_id = request.GET.get("creative_id")
    slot = request.GET.get("slot", "")
    mac = request.GET.get("mac", "")

    # Basic validation of target URL
    if not target or not (target.startswith("http://") or target.startswith("https://")):
        return JsonResponse({"ok": False, "error": "invalid_target"}, status=400)

    try:
        tenant = Tenant.objects.get(id=int(tenant_id)) if tenant_id else None
        site = Site.objects.get(id=int(site_id), tenant=tenant) if tenant and site_id else None
    except (Tenant.DoesNotExist, Site.DoesNotExist):
        tenant = None
        site = None

    if tenant and site:
        try:
            Event.objects.create(
                tenant=tenant,
                site=site,
                type="click",
                payload_json={
                    "slot": slot,
                    "creative_id": int(creative_id) if (creative_id and creative_id.isdigit()) else None,
                    "mac": mac,
                    "target": target,
                },
            )
        except Exception:
            # avoid blocking the redirect on logging errors
            pass

    return HttpResponseRedirect(target)
