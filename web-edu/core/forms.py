from urllib.parse import urlsplit

from django import forms
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import auth
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.validators import FileExtensionValidator

from users.models import UserProfile

User = auth.get_user_model()


def validate_avatar_size(file):
    if file.size > 5 * 1024 * 1024:
        raise forms.ValidationError("Размер аватара не должен превышать 5 МБ.")


class AvatarFormMixin:
    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and avatar.image.format not in {"PNG", "JPEG"}:
            raise forms.ValidationError("Выберите изображение PNG или JPEG.")
        return avatar

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(strip=False)

    next = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_next(self):
        next_url = self.cleaned_data.get("next", "")

        if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=set(), require_https=True):
            return next_url

        return reverse("questions:index")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            self.user = auth.authenticate(username=username, password=password)

            if self.user is None:
                raise forms.ValidationError("Неверный логин или пароль. Попробуйте ещё раз.")

        return cleaned_data

class LogoutForm(forms.Form):
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_next(self):
        next_url = self.cleaned_data.get("next", "")

        if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=set(), require_https=True):
            if urlsplit(next_url).path != reverse("core:profile"):
                return next_url

        return reverse("questions:index")

class SignupForm(AvatarFormMixin, forms.ModelForm):
    avatar = forms.ImageField(required=False, validators=[FileExtensionValidator(["png", "jpg", "jpeg"]), validate_avatar_size])
    email = forms.EmailField(max_length=254, required=False)
    nickname = forms.CharField(max_length=50)
    password = forms.CharField(strip=False, widget=forms.PasswordInput())
    password_repeat = forms.CharField(strip=False, widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")

        if password and password_repeat:
            if password != password_repeat:
                self.add_error("password_repeat", "Пароли не совпадают.")

        if password:
            user = User(username = cleaned_data.get("username", ""), email=cleaned_data.get("email", ""))

            try:
                validate_password(password, user=user)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

            UserProfile.objects.create(
                user=user,
                name=self.cleaned_data["nickname"],
                avatar=self.cleaned_data.get("avatar") or "",
            )

        return user

class ProfileForm(AvatarFormMixin, forms.ModelForm):
    avatar = forms.ImageField(required=False, validators=[FileExtensionValidator(["png", "jpg", "jpeg"]), validate_avatar_size])
    email = forms.EmailField(max_length=254, required=False)
    nickname = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        profile = getattr(self.instance, "userprofile", None)

        if profile is not None:
            self.initial["nickname"] = profile.name

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:

            defaults = {"name": self.cleaned_data["nickname"]}
            if self.cleaned_data.get("avatar"):
                defaults["avatar"] = self.cleaned_data["avatar"]
            UserProfile.objects.update_or_create(user=user, defaults=defaults)

        return user
