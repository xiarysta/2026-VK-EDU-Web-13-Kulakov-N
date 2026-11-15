from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

class QuestionManager(models.Manager):

    def with_rating(self):
        from .models import QuestionVote
    
        votes = (
            QuestionVote.objects.filter(question_id=OuterRef("pk")) \
                .order_by().values("question_id").annotate(total=Sum("value")).values("total")
        )
    
        return self.get_queryset().annotate(rating=Coalesce(Subquery(votes), 0))

    def with_details(self):
        return self.with_rating().annotate(answers_count=Count("answer")) \
            .prefetch_related("tags")

    def new(self):
        return self.with_details().order_by("-created_at", "-id")

    def hot(self):
        return self.with_details().order_by("-rating", "-created_at", "-id")

    def by_tag(self, tag_name):
        
        return self.with_details().filter(tags__name=tag_name).order_by("-created_at", "-id")

class AnswerManager(models.Manager):

    def with_rating(self):
        from .models import AnswerVote

        votes = (
            AnswerVote.objects.filter(answer_id=OuterRef("pk")) \
                .order_by().values("answer_id").annotate(total=Sum("value")).values("total")
        )

        return self.get_queryset().annotate(rating=Coalesce(Subquery(votes), 0))

    def for_question(self, question_id):
        return self.with_rating().filter(question_id=question_id).order_by("created_at", "id")