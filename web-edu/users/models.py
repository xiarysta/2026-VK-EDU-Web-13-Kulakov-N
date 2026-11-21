from django.contrib import auth
from django.conf import settings
from django.db import models
from uuid import uuid4
from pathlib import Path


def avatar_upload_path(instance, filename):
    return f"avatars/{uuid4().hex}{Path(filename).suffix.lower()}"

User = auth.get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    name = models.CharField(max_length=50, verbose_name="Имя")
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to=avatar_upload_path,
        blank=True
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.name} — пользователь #{self.user_id}"
