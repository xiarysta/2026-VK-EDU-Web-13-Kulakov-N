from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

class QuestionManager(models.Manager):

    def with_rating(self):
        from .models import QuestionVote
    
        votes = (
            QuestionVote.objects.filter(question_id=OuterRef("pk")) \
                .order_by().values("question_id").annotate(total=Sum("value")).values("total")
        )
    
        return self.get_queryset().annotate(rating=Coalesce(Subquery(votes), 0))

    def with_details(self, user=None):
        from .models import QuestionVote

        questions = self.with_rating().annotate(answers_count=Count("answer")) \
            .select_related("user__userprofile").prefetch_related("tags")

        if user and user.is_authenticated:
            votes = QuestionVote.objects.filter(user=user, question_id=OuterRef("pk")).values("value")[:1]
            return questions.annotate(user_vote=Coalesce(Subquery(votes), 0))
        return questions.annotate(user_vote=Value(0))

    def new(self, user=None):
        return self.with_details(user=user).order_by("-created_at", "-id")

    def hot(self, user=None):
        return self.with_details(user=user).order_by("-rating", "-created_at", "-id")

    def by_tag(self, tag_name, user=None):
        
        return self.with_details(user=user).filter(tags__name=tag_name).order_by("-created_at", "-id")

class AnswerManager(models.Manager):

    def with_rating(self):
        from .models import AnswerVote

        votes = (
            AnswerVote.objects.filter(answer_id=OuterRef("pk")) \
                .order_by().values("answer_id").annotate(total=Sum("value")).values("total")
        )

        return self.get_queryset().annotate(rating=Coalesce(Subquery(votes), 0))

    def for_question(self, question_id, user=None):
        from .models import AnswerVote

        answers = self.with_rating().select_related("user__userprofile") \
            .filter(question_id=question_id).order_by("created_at", "id")

        if user and user.is_authenticated:
            votes = AnswerVote.objects.filter(user=user, answer_id=OuterRef("pk")).values("value")[:1]
            return answers.annotate(user_vote=Coalesce(Subquery(votes), 0))
        return answers.annotate(user_vote=Value(0))
