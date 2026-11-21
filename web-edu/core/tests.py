from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import UserProfile

User = get_user_model()


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nikita", email="nikita@example.com")
        self.profile = UserProfile.objects.create(user=self.user, name="Никита")
        self.client.force_login(self.user)
        self.url = reverse("core:profile")

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
        self.assertRedirects(self.client.get(self.url), reverse("core:login") + "?next=" + self.url)

    def test_save_after_session_expires_redirects_to_login(self):
        self.client.logout()
        response = self.client.post(self.url, {"email": "new@example.com", "nickname": "Имя"})
        self.assertRedirects(response, reverse("core:login") + "?next=" + self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "nikita@example.com")

    def test_logout_from_profile_redirects_to_home(self):
        response = self.client.post(reverse("core:logout"), {"next": self.url + "?tab=settings"}, follow=True)
        self.assertRedirects(response, reverse("questions:index"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_keeps_public_next_page(self):
        response = self.client.post(reverse("core:logout"), {"next": reverse("questions:hot")})
        self.assertRedirects(response, reverse("questions:hot"))

    def test_logout_rejects_external_redirect(self):
        response = self.client.post(reverse("core:logout"), {"next": "https://example.com/"})
        self.assertRedirects(response, reverse("questions:index"))
