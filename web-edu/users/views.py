from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import LoginForm, LogoutForm, SignupForm, ProfileForm
from django.contrib import auth
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# Create your views here.
def login(request):

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            auth.login(request, form.user)
            return HttpResponseRedirect(form.cleaned_data["next"])

    else:
       form = LoginForm(initial={"next": request.GET.get("next", "")})
  
    return render(request, "users/login.html", context={"form": form, "demo_authenticated": False})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user=user)

            return HttpResponseRedirect(reverse("questions:index"))

    else:
        form = SignupForm()


    return render(request, "users/signup.html", context={"form": form})

@login_required
def profile(request):
    if (request.method == 'POST'):
        form = ProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse("users:profile"))

    else:
        form = ProfileForm(instance=request.user)
  
    return render(request, "users/profile.html", context={"form": form})

@require_POST
def logout(request):
    form = LogoutForm(request.POST)

    if form.is_valid():
        next_url = form.cleaned_data["next"]
    else:
       next_url = reverse("questions:index")

    auth.logout(request)

    return HttpResponseRedirect(next_url)

    




   

