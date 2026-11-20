from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Project


class ProjectTests(BaseAPITestCase):
    url = "/My-Own/projects/"
    payload = {
        "title": "Portfolio",
        "description": "My site",
        "tech_stack": "React, Django",
        "live_link": "https://example.com",
        "repo_link": "https://github.com/example/repo",
    }

    def test_public_list_newest_first(self):
        Project.objects.create(title="Old", description="d", tech_stack="t")
        Project.objects.create(title="New", description="d", tech_stack="t")
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual([p["title"] for p in res.json()], ["New", "Old"])
        self.assertIn("image_url", res.json()[0])
        self.assertIsNone(res.json()[0]["image_url"])

    def test_only_admin_can_create(self):
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 401)
        self.auth(self.user)
        self.assertEqual(self.client.post(self.url, self.payload, format="json").status_code, 403)
        self.auth(self.admin)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(Project.objects.get().title, "Portfolio")

    def test_invalid_url_rejected(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {**self.payload, "live_link": "not a url"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_detail_update_delete_admin_only(self):
        project = Project.objects.create(title="P", description="d", tech_stack="t")
        detail = f"{self.url}{project.id}/"
        self.auth(self.user)
        self.assertEqual(self.client.patch(detail, {"title": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(detail).status_code, 403)
        self.auth(self.admin)
        self.assertEqual(self.client.patch(detail, {"title": "Renamed"}, format="json").json()["title"], "Renamed")
        self.assertEqual(self.client.delete(detail).status_code, 204)
