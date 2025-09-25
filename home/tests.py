from django.test import Client, TestCase


class HomeViewTests(TestCase):
    def test_home_page_renders(self):
        client = Client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Portal OpenWISP")
