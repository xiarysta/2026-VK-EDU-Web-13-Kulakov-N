from django.urls import path
from .views import index, hot, tag, question_detail

app_name = "questions"

urlpatterns = [
  path('', index, name="index"),
  path('hot/', hot, name="hot"),
  path('tag/<str:tag_name>/', tag, name="tag_detail"),
  path('question/<int:question_id>/', question_detail, name="question_detail"),

]