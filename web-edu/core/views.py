from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import LoginForm, LogoutForm, ProfileForm, SignupForm


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            auth.login(request, form.user)
            return HttpResponseRedirect(form.cleaned_data["next"])
    else:
        form = LoginForm(initial={"next": request.GET.get("next", "")})
    return render(request, "core/login.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return HttpResponseRedirect(reverse("questions:index"))
    else:
        form = SignupForm()
    return render(request, "core/signup.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("core:profile"))
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "core/profile.html", {"form": form})


@require_POST
def logout(request):
    form = LogoutForm(request.POST)
    next_url = form.cleaned_data["next"] if form.is_valid() else reverse("questions:index")
    auth.logout(request)
    return HttpResponseRedirect(next_url)
