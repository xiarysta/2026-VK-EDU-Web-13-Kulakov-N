from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import UserProfile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="member", password="Strong-local-pass-761")

    def test_login_respects_local_next_and_rejects_external_urls(self):
        for next_url, expected in (("/hot/?page=2", "/hot/?page=2"), ("https://example.com/", "/"), ("//example.com/", "/")):
            self.client.logout()
            response = self.client.post(reverse("core:login"), {"username": "member", "password": "Strong-local-pass-761", "next": next_url})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, expected)
            self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_shows_error_and_keeps_username(self):
        response = self.client.post(reverse("core:login"), {"username": "member", "password": "incorrect", "next": "/hot/"})
        self.assertContains(response, "Неверный логин или пароль")
        self.assertContains(response, 'value="member"')
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_signup_creates_user_and_profile_and_logs_in(self):
        response = self.client.post(reverse("core:signup"), {"username": "new_member", "email": "new@example.com", "nickname": "Новое имя", "password": "Secure-pass-5729", "password_repeat": "Secure-pass-5729"})
        self.assertRedirects(response, "/")
        user = get_user_model().objects.get(username="new_member")
        self.assertTrue(user.check_password("Secure-pass-5729"))
        self.assertEqual(UserProfile.objects.get(user=user).name, "Новое имя")
        self.assertIn("_auth_user_id", self.client.session)

    def test_signup_rejects_weak_or_mismatched_password(self):
        for password, repeated in (("123", "123"), ("Secure-pass-5729", "different")):
            response = self.client.post(reverse("core:signup"), {"username": "new_member", "nickname": "Имя", "password": password, "password_repeat": repeated})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertContains(response, 'value="new_member"')
            self.assertFalse(get_user_model().objects.filter(username="new_member").exists())
