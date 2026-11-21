from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image

from .models import UserProfile

User = get_user_model()


class SignupAvatarTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        settings_override = override_settings(MEDIA_ROOT=media.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.media_root = Path(media.name)
        self.data = {
            "username": "new_user", "email": "new@example.com", "nickname": "Новое имя",
            "password": "R7!q2#M9v5$Z", "password_repeat": "R7!q2#M9v5$Z",
        }

    def avatar(self, name="avatar.png", image_format="PNG", oversized=False):
        content = BytesIO()
        Image.new("RGB", (2, 2)).save(content, format=image_format)
        data = content.getvalue()
        if oversized:
            data += b"\0" * (5 * 1024 * 1024)
        return SimpleUploadedFile(name, data, content_type="image/" + image_format.lower())

    def test_signup_saves_uploaded_avatar_and_displays_it(self):
        response = self.client.post(reverse("users:signup"), {**self.data, "avatar": self.avatar()})
        self.assertRedirects(response, reverse("questions:index"))
        user = User.objects.get(username="new_user")
        avatar = user.userprofile.avatar
        self.assertTrue((self.media_root / avatar.name).is_file())
        self.assertRegex(avatar.name, r"^avatars/[0-9a-f]{32}\.png$")
        self.assertContains(self.client.get(reverse("users:profile")), avatar.url)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_without_avatar_uses_placeholder(self):
        response = self.client.post(reverse("users:signup"), self.data)
        self.assertRedirects(response, reverse("questions:index"))
        self.assertFalse(User.objects.get(username="new_user").userprofile.avatar)
        self.assertContains(self.client.get(reverse("users:profile")), "pumpkin.svg")

    def test_invalid_avatars_show_errors_and_do_not_create_user(self):
        for name, image_format, oversized in (
            ("avatar.gif", "GIF", False),
            ("avatar.jpg", "GIF", False),
            ("avatar.txt", "PNG", False),
            ("avatar.png", "PNG", True),
        ):
            with self.subTest(name=name, image_format=image_format, oversized=oversized):
                response = self.client.post(reverse("users:signup"), {
                    **self.data, "avatar": self.avatar(name, image_format, oversized),
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors.get("avatar"))
                self.assertContains(response, 'id="register-avatar-errors"')
                self.assertContains(response, 'value="new_user"')
                self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_profile_uses_same_avatar_validation(self):
        user = User.objects.create_user(username="existing_user")
        UserProfile.objects.create(user=user, name="Имя")
        self.client.force_login(user)
        for oversized, image_format in ((False, "GIF"), (True, "PNG")):
            response = self.client.post(reverse("users:profile"), {
                "nickname": "Имя", "email": "", "avatar": self.avatar("avatar.png", image_format, oversized),
            })
            self.assertTrue(response.context["form"].errors.get("avatar"))
            self.assertContains(response, 'id="avatar-error"')
        self.assertFalse(UserProfile.objects.get(user=user).avatar)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nikita", email="nikita@example.com")
        self.profile = UserProfile.objects.create(user=self.user, name="Никита")
        self.client.force_login(self.user)
        self.url = reverse("users:profile")

    def test_get_shows_current_values_without_errors(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'value="nikita"')
        self.assertContains(response, 'value="nikita@example.com"')
        self.assertContains(response, 'value="Никита"')
        self.assertNotContains(response, 'role="alert"')
        self.assertNotContains(response, 'aria-invalid="true"')

    def test_invalid_email_shows_real_error_and_preserves_input(self):
        response = self.client.post(self.url, {"email": "bad-email", "nickname": "Новое имя"})
        self.assertFormError(response.context["form"], "email", "Введите правильный адрес электронной почты.")
        self.assertContains(response, 'id="email-error"')
        self.assertContains(response, 'value="bad-email"')
        self.assertContains(response, 'value="Новое имя"')
        self.assertNotContains(response, "Этот email уже используется")
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.email, "nikita@example.com")
        self.assertEqual(self.profile.name, "Никита")

    def test_required_nickname_error_is_visible(self):
        response = self.client.post(self.url, {"email": "", "nickname": ""})
        self.assertContains(response, 'id="nickname-error"')
        self.assertContains(response, "Обязательное поле.")

    def test_save_and_reload_current_data(self):
        response = self.client.post(self.url, {"email": "new@example.com", "nickname": "Новое имя"}, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, 'value="new@example.com"')
        self.assertContains(response, 'value="Новое имя"')
        self.assertNotContains(response, 'aria-invalid="true"')
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.profile.name, "Новое имя")

    def test_anonymous_profile_redirects_to_existing_login_page(self):
        self.client.logout()
        self.assertRedirects(self.client.get(self.url), reverse("users:login") + "?next=" + self.url)

    def test_save_after_session_expires_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"email": "new@example.com", "nickname": "Имя"})
        self.assertRedirects(response, reverse("users:login") + "?next=" + self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "nikita@example.com")

    def test_logout_from_profile_redirects_to_home(self):
        response = self.client.post(reverse("users:logout"), {"next": self.url + "?tab=settings"}, follow=True)
        self.assertRedirects(response, reverse("questions:index"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_keeps_public_next_page(self):
        response = self.client.post(reverse("users:logout"), {"next": reverse("questions:hot")})
        self.assertRedirects(response, reverse("questions:hot"))

    def test_logout_rejects_external_redirect(self):
        response = self.client.post(reverse("users:logout"), {"next": "https://example.com/"})
        self.assertRedirects(response, reverse("questions:index"))
