from django.urls import path
from .views import index, hot, tag, question_detail, ask
from . import api

app_name = "questions"

urlpatterns = [
  path('api/questions/vote/', api.question_vote, name="question_vote"),
  path('api/answers/vote/', api.answer_vote, name="answer_vote"),
  path('api/answers/correct/', api.correct_answer, name="correct_answer"),
  path('', index, name="index"),
  path('hot/', hot, name="hot"),
  path('tag/<str:tag_name>/', tag, name="tag_detail"),
  path('question/<int:question_id>/', question_detail, name="question_detail"),
  path('ask/', ask, name="ask"),

]
