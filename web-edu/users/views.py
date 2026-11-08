from django.shortcuts import render

# Create your views here.
def login(request):
  return render(request, "users/login.html", context={"demo_authenticated": False})

def signup(request):
  return render(request, "users/signup.html", context={"demo_authenticated": False})

def profile(request):
  return render(request, "users/profile.html", context={"demo_authenticated": True})
