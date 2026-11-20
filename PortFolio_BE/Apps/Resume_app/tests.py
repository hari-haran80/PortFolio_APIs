import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Resume

TMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class ResumeTests(BaseAPITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def pdf(self, name="cv.pdf", content=b"%PDF-1.4 test"):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def test_download_404_when_missing(self):
        self.assertEqual(self.client.get("/Resume/download/").status_code, 404)

    def test_only_admin_can_upload(self):
        self.assertEqual(self.client.post("/Resume/upload/", {"file": self.pdf()}).status_code, 401)
        self.auth(self.user)
        self.assertEqual(self.client.post("/Resume/upload/", {"file": self.pdf()}).status_code, 403)
        self.assertFalse(Resume.objects.exists())

    def test_upload_replaces_and_download_works(self):
        self.auth(self.admin)
        self.assertEqual(self.client.post("/Resume/upload/", {"file": self.pdf("old.pdf")}).status_code, 201)
        res = self.client.post("/Resume/upload/", {"file": self.pdf("new.pdf", b"%PDF new")})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Resume.objects.count(), 1)

        self.logout()
        res = self.client.get("/Resume/download/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"".join(res.streaming_content), b"%PDF new")
        disposition = res["Content-Disposition"]
        self.assertIn("attachment", disposition)
        self.assertNotIn("resumes/", disposition)

    def test_rejects_bad_type_and_missing_file_without_deleting_existing(self):
        self.auth(self.admin)
        self.client.post("/Resume/upload/", {"file": self.pdf()})
        res = self.client.post("/Resume/upload/", {"file": SimpleUploadedFile("evil.exe", b"MZ")})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(self.client.post("/Resume/upload/", {}).status_code, 400)
        self.assertEqual(Resume.objects.count(), 1)
