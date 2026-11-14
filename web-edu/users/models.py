from django.contrib import auth
from django.conf import settings
from django.db import models

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
        upload_to="avatars/",
        blank=True
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
