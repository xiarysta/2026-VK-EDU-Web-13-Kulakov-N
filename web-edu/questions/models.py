from django.db import models
from django.conf import settings
from django.db.models.constraints import UniqueConstraint, CheckConstraint
from .managers import QuestionManager, AnswerManager

class Question(models.Model):
    objects = QuestionManager()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор вопроса"
    )

    tags = models.ManyToManyField(
        "Tag",
        through="QuestionTag",
        related_name="questions",
        verbose_name="Теги",
        blank=True
    )

    title = models.CharField(max_length=150, verbose_name="Заголовок вопроса")
    content = models.TextField(verbose_name="Текст вопроса")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return f"Вопрос #{self.id}: {self.title}"

class Answer(models.Model):
    objects = AnswerManager()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор ответа"
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name="Вопрос"
    )

    content = models.TextField(verbose_name="Текст ответа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_correct = models.BooleanField(verbose_name="Правильный ответ?", default=False)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ #{self.id}: {' '.join(self.content.split())[:50]}"

class AnswerVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Кто проголосовал"
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
        verbose_name = "Голос за ответ"
        verbose_name_plural = "Голоса за ответы"
        constraints = [
            UniqueConstraint(
                name="unique_answer_vote", fields=["user", "answer"]
            ),

            CheckConstraint(
                name="valid_answer_vote_value",
                condition=models.Q(value__in=[-1, 1])
            )
        ]

    def __str__(self):
        return f"Ответ #{self.answer_id}: {self.value:+d}, пользователь #{self.user_id}"

class QuestionVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Кто проголосовал"
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
        verbose_name = "Голос за вопрос"
        verbose_name_plural = "Голоса за вопросы"
        constraints = [
            UniqueConstraint(
                name="unique_question_vote", fields=["user", "question"]
            ),

            CheckConstraint(
                name="valid_question_vote_value",
                condition=models.Q(value__in=[-1, 1])
            )
        ]

    def __str__(self):
        return f"Вопрос #{self.question_id}: {self.value:+d}, пользователь #{self.user_id}"

class Tag(models.Model):
    name = models.CharField(max_length=35, unique=True, verbose_name="Название тега")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

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
        verbose_name = "Связь вопроса с тегом"
        verbose_name_plural = "Связи вопросов с тегами"

        constraints = [
            UniqueConstraint(
                name="unique_question_tag", fields=["question", "tag"]
            )
        ]

    def __str__(self):
        return f"Вопрос #{self.question_id} — тег #{self.tag_id}"
