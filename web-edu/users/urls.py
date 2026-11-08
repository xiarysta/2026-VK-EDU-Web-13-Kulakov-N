from django.urls import path

from .views import login, signup, profile

app_name = "users"

urlpatterns = [
    path('login/', login, name="login"),
    path('signup/', signup, name="signup"),
    path('profile/', profile, name="profile"),
]
