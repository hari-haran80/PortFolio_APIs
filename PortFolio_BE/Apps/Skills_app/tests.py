from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Skill, SkillCategory


class SkillTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.category = SkillCategory.objects.create(name="Backend")
        self.skill = Skill.objects.create(category=self.category, name="Django", fluency=90)

    def test_public_can_read_categories_with_nested_skills(self):
        res = self.client.get("/api/skill-categories/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()[0]["skills"][0]["name"], "Django")
        self.assertEqual(self.client.get("/api/skills/").status_code, 200)

    def test_anonymous_and_users_cannot_modify(self):
        for user in (None, self.user):
            if user:
                self.auth(user)
            self.assertIn(self.client.post("/api/skill-categories/", {"name": "X"}, format="json").status_code, (401, 403))
            self.assertIn(self.client.delete(f"/api/skills/{self.skill.id}/").status_code, (401, 403))
            self.assertIn(
                self.client.patch(f"/api/skills/{self.skill.id}/", {"fluency": 1}, format="json").status_code, (401, 403)
            )
        self.assertTrue(Skill.objects.filter(id=self.skill.id, fluency=90).exists())

    def test_admin_crud(self):
        self.auth(self.admin)
        res = self.client.post("/api/skill-categories/", {"name": "Frontend"}, format="json")
        self.assertEqual(res.status_code, 201)
        cat_id = res.json()["id"]
        res = self.client.post("/api/skills/", {"category": cat_id, "name": "React", "fluency": 80}, format="multipart")
        self.assertEqual(res.status_code, 201, res.content)
        skill_id = res.json()["id"]
        res = self.client.patch(f"/api/skills/{skill_id}/", {"fluency": 85}, format="multipart")
        self.assertEqual(res.json()["fluency"], 85)
        self.assertEqual(self.client.delete(f"/api/skills/{skill_id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/skill-categories/{cat_id}/").status_code, 204)
