from django.urls import path
from .views import index, hot

app_name = "questions"

urlpatterns = [
  path('', index, name="index"),
  path('hot/', hot, name="hot")
]