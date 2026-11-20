from datetime import date
from unittest import mock

from django.core.cache import cache
from django.test import override_settings

from Apps.Authentication_App.testing import BaseAPITestCase
from .models import AboutMe, Education, Experience, Language
from . import views


def make_about():
    return AboutMe.objects.create(
        name="Hari", phone_number="123", linkedin_id="https://linkedin.com/in/x",
        nationality="Indian", email="hari@example.com",
    )


class ExperienceCalculationTests(BaseAPITestCase):
    def test_no_experience(self):
        self.assertEqual(make_about().experience, "0 months")

    def test_months_and_years(self):
        about = make_about()
        Experience.objects.create(title="Dev", company="A", start_date=date(2020, 1, 1), end_date=date(2020, 7, 1))
        about.refresh_from_db()
        self.assertEqual(about.experience, "6 months")
        Experience.objects.create(title="Dev", company="B", start_date=date(2021, 1, 1), end_date=date(2023, 1, 1))
        about.refresh_from_db()
        self.assertEqual(about.experience, "2.5 years")

    def test_delete_experience_recalculates(self):
        about = make_about()
        exp = Experience.objects.create(title="Dev", company="A", start_date=date(2020, 1, 1), end_date=date(2021, 1, 1))
        exp.delete()
        about.refresh_from_db()
        self.assertEqual(about.experience, "0 months")


class AboutPermissionTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.about = make_about()
        Language.objects.create(about_me=self.about, name="English", level="Fluent", proficiency=90)
        Education.objects.create(degree="BE", institution="Uni", start_year=2016, end_year=2020)

    def test_public_reads(self):
        for path in ("/about/about-me/", "/about/languages/", "/about/experience/", "/about/education/"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        body = self.client.get("/about/about-me/").json()[0]
        self.assertEqual(body["languages"][0]["name"], "English")
        self.assertIn("experience", body)

    def test_anonymous_and_users_cannot_write(self):
        for user in (None, self.user):
            if user:
                self.auth(user)
            res = self.client.patch(f"/about/about-me/{self.about.id}/", {"name": "Hacked"}, format="json")
            self.assertIn(res.status_code, (401, 403))
            res = self.client.post("/about/education/", {
                "degree": "x", "institution": "y", "start_year": 1, "end_year": 2,
            }, format="json")
            self.assertIn(res.status_code, (401, 403))
            self.assertIn(self.client.delete(f"/about/about-me/{self.about.id}/").status_code, (401, 403))
        self.about.refresh_from_db()
        self.assertEqual(self.about.name, "Hari")

    def test_experience_field_is_read_only(self):
        self.auth(self.admin)
        res = self.client.patch(f"/about/about-me/{self.about.id}/", {"experience": "99 years"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["experience"], "0 months")

    def test_admin_crud(self):
        self.auth(self.admin)
        res = self.client.post("/about/experience/", {
            "title": "Dev", "company": "Co", "start_date": "2022-01-01", "end_date": "2023-01-01",
        }, format="json")
        self.assertEqual(res.status_code, 201, res.content)
        exp_id = res.json()["id"]
        self.assertEqual(self.client.patch(f"/about/experience/{exp_id}/", {"title": "Lead"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/about/experience/{exp_id}/").status_code, 204)


class FakeResponse:
    def __init__(self, status_code=200, data=None, headers=None, text=""):
        self.status_code = status_code
        self._data = data
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._data


@override_settings(GITHUB_TOKEN="test-token", GITHUB_USERNAME="tester")
class TotalCommitsTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def fake_get(self, url, headers=None, params=None, timeout=None):
        if url.endswith("/user/repos"):
            return FakeResponse(data=[
                {"name": "big", "full_name": "tester/big", "private": False, "html_url": "u1"},
                {"name": "small", "full_name": "tester/small", "private": True, "html_url": "u2"},
                {"name": "empty", "full_name": "tester/empty", "private": False, "html_url": "u3"},
            ])
        if "tester/big" in url:
            return FakeResponse(headers={
                "Link": '<https://api.github.com/repositories/1/commits?per_page=1&page=2>; rel="next", '
                        '<https://api.github.com/repositories/1/commits?per_page=1&page=120>; rel="last"'
            }, data=[{}])
        if "tester/small" in url:
            return FakeResponse(data=[{}])  # single commit, no Link header
        return FakeResponse(status_code=409, data={"message": "Git Repository is empty."})

    def test_counts_commits_and_caches(self):
        with mock.patch.object(views.requests, "get", side_effect=self.fake_get) as m:
            res = self.client.get("/about/total-commits/")
            self.assertEqual(res.status_code, 200, res.content)
            body = res.json()
            self.assertEqual(body["total_commits"], 121)
            self.assertEqual(body["repository_count"], 3)
            self.assertEqual(body["private_repos_count"], 1)
            calls = m.call_count
            # Second call is served from cache, no GitHub traffic.
            self.assertEqual(self.client.get("/about/total-commits/").json()["total_commits"], 121)
            self.assertEqual(m.call_count, calls)

    def test_github_failure_returns_502(self):
        with mock.patch.object(views.requests, "get", return_value=FakeResponse(401, {"message": "Bad credentials"})):
            res = self.client.get("/about/total-commits/")
        self.assertEqual(res.status_code, 502)
        self.assertEqual(res.json()["github_error"], "Bad credentials")

    @override_settings(GITHUB_TOKEN="")
    def test_missing_token(self):
        self.assertEqual(self.client.get("/about/total-commits/").status_code, 503)

    def test_link_header_parser(self):
        self.assertEqual(views._last_page_from_link_header(
            '<https://x/commits?per_page=1&page=7>; rel="last"'), 7)
        self.assertIsNone(views._last_page_from_link_header(""))
