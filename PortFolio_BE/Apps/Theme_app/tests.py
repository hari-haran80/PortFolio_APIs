from Apps.Authentication_App.testing import BaseAPITestCase, STRONG_PASSWORD


class ThemeTests(BaseAPITestCase):
    def test_requires_auth(self):
        self.assertEqual(self.client.get("/User/api/theme/").status_code, 401)
        self.assertEqual(self.client.post("/User/api/theme/set/", {"theme": "dark"}).status_code, 401)

    def test_default_is_light_then_set_dark(self):
        self.auth(self.user)
        self.assertEqual(self.client.get("/User/api/theme/").json(), {"theme": "light"})
        res = self.client.post("/User/api/theme/set/", {"theme": "dark"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.client.get("/User/api/theme/").json(), {"theme": "dark"})

    def test_invalid_theme_rejected(self):
        self.auth(self.user)
        self.assertEqual(self.client.post("/User/api/theme/set/", {"theme": "purple"}, format="json").status_code, 400)

    def test_login_returns_saved_theme(self):
        self.auth(self.user)
        self.client.post("/User/api/theme/set/", {"theme": "dark"}, format="json")
        self.logout()
        res = self.client.post("/Auth/login/", {"username": "alice", "password": STRONG_PASSWORD}, format="json")
        self.assertEqual(res.json()["theme"], {"theme": "dark"})

    def test_themes_are_per_user(self):
        self.auth(self.user)
        self.client.post("/User/api/theme/set/", {"theme": "dark"}, format="json")
        self.auth(self.other)
        self.assertEqual(self.client.get("/User/api/theme/").json(), {"theme": "light"})
