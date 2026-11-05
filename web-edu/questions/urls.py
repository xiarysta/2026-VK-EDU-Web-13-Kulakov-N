from django.urls import path
from .views import index, hot, tag

app_name = "questions"

urlpatterns = [
  path('', index, name="index"),
  path('hot/', hot, name="hot"),
  path('tag/<str:tag_name>/', tag, name="tag_detail"),

]