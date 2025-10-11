from django.contrib.auth.models import User
from django.test import Client, TestCase

from ads.decision import decide_ad  # noqa: F401 imported for future tests
from contentmgmt.models import Page, PageRevision
from core.models import SSID, Brand, Controller, Site, Tenant


class PortalTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T1")
        self.brand = Brand.objects.create(tenant=self.tenant, name="B1")
        self.site = Site.objects.create(tenant=self.tenant, brand=self.brand, name="S1")
        Page.objects.create(
            tenant=self.tenant,
            brand=self.brand,
            site=self.site,
            name="P1",
            status="published",
            html="<html><body>P1</body></html>",
        )
        # Controller + SSID for phase 4 tests (test mode)
        self.controller = Controller.objects.create(
            tenant=self.tenant,
            type="ruckus_sz",
            base_url="https://example.invalid",
        )
        self.ssid = SSID.objects.create(
            site=self.site, name="GuestWiFi", controller=self.controller
        )

    def test_splash_endpoint(self):
        c = Client()
        resp = c.get(
            f"/p/{self.tenant.id}/{self.site.id}"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"P1", resp.content)

    def test_admin_api_tenants(self):
        # Authenticate as staff per DRF IsAdminUser default permissions
        staff = User.objects.create_user(username="admin", email="a@b.com", password="x")
        staff.is_staff = True
        staff.save()
        c = Client()
        c.login(username="admin", password="x")
        resp = c.get("/api/admin/tenants/", HTTP_X_TENANT_ID=str(self.tenant.id))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)

    def test_clickthrough_auth(self):
        c = Client()
        resp = c.post(
            "/auth/clickthrough",
            {"tenant_id": self.tenant.id, "site_id": self.site.id, "mac": "aa:bb:cc:dd:ee:ff"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_email_otp_flow(self):
        from authsvc.models import EmailOTP

        c = Client()
        start = c.post("/auth/email-otp", {"tenant_id": self.tenant.id, "email": "a@b.com"}).json()
        code = start.get("dev_code")
        if not code:
            code = EmailOTP.objects.get(id=start["otp_id"]).code
        verify = c.post(
            "/auth/email-otp/verify",
            {
                "tenant_id": self.tenant.id,
                "site_id": self.site.id,
                "mac": "aa:bb:cc:dd:ee:11",
                "email": "a@b.com",
                "code": code,
            },
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["ok"])

    def test_voucher_auth(self):
        from authsvc.models import Voucher

        Voucher.objects.create(tenant=self.tenant, code="ABC123")
        c = Client()
        resp = c.post(
            "/auth/voucher",
            {
                "tenant_id": self.tenant.id,
                "site_id": self.site.id,
                "mac": "aa:bb:cc:dd:ee:22",
                "code": "ABC123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_wispr_login_success(self):
        c = Client()
        resp = c.post(
            "/ruckus/wispr/login",
            {
                "tenant_id": self.tenant.id,
                "site_id": self.site.id,
                "ssid": self.ssid.name,
                "mac": "aa:bb:cc:dd:ee:33",
                "minutes": 30,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login Succeeded", resp.content)

    def test_decision_frequency_cap(self):
        # First three decisions should return a creative; fourth should be capped
        c = Client()
        mac = "aa:bb:cc:dd:ee:44"
        # Create an active campaign/creative via API (auth as staff)
        staff = User.objects.create_user(username="admin2", email="b@b.com", password="x")
        staff.is_staff = True
        staff.save()
        c.login(username="admin2", password="x")
        # Create a campaign and creative
        resp = c.post(
            "/api/admin/campaigns/",
            {"tenant": self.tenant.id, "name": "Camp1", "status": "active"},
        )
        self.assertEqual(resp.status_code, 201)
        camp_id = resp.json()["id"]
        resp = c.post(
            "/api/admin/creatives/",
            {
                "campaign": camp_id,
                "type": "image",
                "asset_url": "https://example.com/a.png",
                "width": 300,
                "height": 250,
                "click_url": "https://example.com",
            },
        )
        self.assertEqual(resp.status_code, 201)

        for i in range(3):
            resp = c.get(f"/p/{self.tenant.id}/{self.site.id}/ads?slot=hero&mac={mac}")
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(resp.json().get("creative"))
        # Fourth request should be capped (no creative)
        resp = c.get(f"/p/{self.tenant.id}/{self.site.id}/ads?slot=hero&mac={mac}")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.json().get("creative"))

        # Validate daily aggregates recomputation includes impressions
        from datetime import date

        from analytics.models import DailyAggregate
        from analytics.tasks import recompute_daily_for

        recompute_daily_for(date.today())
        agg = DailyAggregate.objects.get(
            date=date.today(), tenant_id=self.tenant.id, site_id=self.site.id
        )
        self.assertGreaterEqual(agg.impressions, 3)

    def test_coa_success(self):
        c = Client()
        resp = c.post(
            "/ruckus/coa",
            {
                "tenant_id": self.tenant.id,
                "site_id": self.site.id,
                "ssid": self.ssid.name,
                "mac": "aa:bb:cc:dd:ee:33",
                "reason": "test",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_page_builder_preview_publish_revision(self):
        # Create staff and page for builder
        staff = User.objects.create_user(username="admin3", email="c@b.com", password="x")
        staff.is_staff = True
        staff.save()
        c = Client()
        c.login(username="admin3", password="x")
        # Create a draft page
        resp = c.post(
            "/api/admin/pages/",
            {
                "tenant": self.tenant.id,
                "brand": self.brand.id,
                "site": self.site.id,
                "name": "Builder Page",
                "status": "draft",
            },
        )
        self.assertEqual(resp.status_code, 201)
        page_id = resp.json()["id"]
        # Save blocks
        blocks = [{"type": "hero", "title": "Hi", "subtitle": "There"}]
        resp = c.post(
            f"/api/admin/pages/{page_id}/save-blocks/",
            data={"blocks": blocks},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        # Preview
        resp = c.get(f"/api/admin/pages/{page_id}/preview/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("<section", resp.json()["html"])
        # Publish now
        resp = c.post(f"/api/admin/pages/{page_id}/publish/", data={})
        self.assertEqual(resp.status_code, 200)
        # Revision created
        self.assertEqual(PageRevision.objects.filter(page_id=page_id).count(), 1)
