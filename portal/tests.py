from django.test import Client, TestCase

from contentmgmt.models import Page
from core.models import Brand, Site, Tenant


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

    def test_splash_endpoint(self):
        c = Client()
        resp = c.get(f"/p/{self.tenant.id}/{self.site.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"P1", resp.content)

    def test_admin_api_tenants(self):
        c = Client()
        resp = c.get("/api/admin/tenants/")
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
        c = Client()
        start = c.post("/auth/email-otp", {"tenant_id": self.tenant.id, "email": "a@b.com"}).json()
        verify = c.post(
            "/auth/email-otp/verify",
            {
                "tenant_id": self.tenant.id,
                "site_id": self.site.id,
                "mac": "aa:bb:cc:dd:ee:11",
                "email": "a@b.com",
                "code": start["dev_code"],
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
