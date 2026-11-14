from django.db import models
from django.conf import settings
from django.db.models.constraints import UniqueConstraint, CheckConstraint

class Question(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )

    tags = models.ManyToManyField(
        "Tag",
        through="QuestionTag",
        related_name="questions",
        verbose_name="Теги",
        blank=True
    )

    title = models.CharField(max_length=150, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Текст вопроса")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан в")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

class Answer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос"
    )

    content = models.TextField(verbose_name="Текст ответа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан в")
    is_correct = models.BooleanField(verbose_name="Правильный ответ", default=False)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

class AnswerVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )

    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        verbose_name="Ответ"
    )

    class ValueType(models.IntegerChoices):
        LIKE = 1, "Лайк (+1)"
        DISLIKE = -1, "Дизлайк (-1)"

    value = models.IntegerField(choices = ValueType.choices, verbose_name="Голос")

    class Meta:
        verbose_name = "Голос на ответ"
        verbose_name_plural = "Голоса на ответы"
        constraints = [
            UniqueConstraint(
                name="unique_answer_vote", fields=["user", "answer"]
            ),

            CheckConstraint(
                name="valid_answer_vote_value",
                condition=models.Q(value__in=[-1, 1])
            )
        ]

class QuestionVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос"
    )

    class ValueType(models.IntegerChoices):
        LIKE = 1, "Лайк (+1)"
        DISLIKE = -1, "Дизлайк (-1)"

    value = models.IntegerField(choices = ValueType.choices, verbose_name="Голос")

    class Meta:
        verbose_name = "Голос на вопрос"
        verbose_name_plural = "Голоса на вопросы"
        constraints = [
            UniqueConstraint(
                name="unique_question_vote", fields=["user", "question"]
            ),

            CheckConstraint(
                name="valid_question_vote_value",
                condition=models.Q(value__in=[-1, 1])
            )
        ]

class Tag(models.Model):
    name = models.CharField(max_length=35, unique=True, verbose_name="Тег")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

class QuestionTag(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос"
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name="Тег"
    )

    class Meta:
        verbose_name = "Тег вопроса"
        verbose_name_plural = "Теги вопроса"

        constraints = [
            UniqueConstraint(
                name="unique_question_tag", fields=["question", "tag"]
            )
        ]
