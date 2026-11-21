from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from users.models import UserProfile
from PIL import Image



class AvatarTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="nikita", email="nikita@example.com")
        self.profile = UserProfile.objects.create(user=self.user, name="Никита")
        self.client.force_login(self.user)
        self.url = reverse("core:profile")
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        override = override_settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)

    def image(self, name="avatar.png", format="PNG"):
        data = BytesIO()
        Image.new("RGB", (2, 2)).save(data, format=format)
        return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

    def test_upload_persists_and_is_displayed(self):
        response = self.client.post(self.url, {"email": "", "nickname": "Имя", "avatar": self.image()}, follow=True)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar.storage.exists(self.profile.avatar.name))
        self.assertRegex(self.profile.avatar.name, r"^avatars/[0-9a-f]{32}\.png$")
        self.assertContains(response, self.profile.avatar.url, count=2)
        saved_name = self.profile.avatar.name
        self.client.post(self.url, {"email": "", "nickname": "Другое имя"})
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar.name, saved_name)

    def test_invalid_file_rejected_without_partial_save(self):
        response = self.client.post(self.url, {"email": "changed@example.com", "nickname": "Имя", "avatar": SimpleUploadedFile("fake.png", b"fake")})
        self.assertTrue(response.context["form"].errors.get("avatar"))
        self.assertContains(response, 'id="avatar-error"')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "nikita@example.com")

    def test_unsupported_format_rejected(self):
        response = self.client.post(self.url, {"email": "", "nickname": "Имя", "avatar": self.image("file.gif", "GIF")})
        self.assertTrue(response.context["form"].errors.get("avatar"))

    def test_oversized_file_rejected(self):
        upload = self.image()
        upload.size = 6 * 1024 * 1024
        from .forms import ProfileForm
        form = ProfileForm({"email": "", "nickname": "Имя"}, {"avatar": upload}, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("5 МБ", str(form.errors["avatar"]))


    def test_avatar_can_be_uploaded_during_signup(self):
        self.client.logout()
        response = self.client.post(reverse("core:signup"), {"username": "avatar_member", "nickname": "Имя", "password": "Secure-pass-5729", "password_repeat": "Secure-pass-5729", "avatar": self.image()})
        self.assertRedirects(response, "/")
        profile = UserProfile.objects.get(user__username="avatar_member")
        self.assertTrue(profile.avatar.storage.exists(profile.avatar.name))
