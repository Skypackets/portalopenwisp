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


from django.test import TestCase

# Create your tests here.
