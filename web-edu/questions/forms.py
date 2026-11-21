from django import forms
from django.db import transaction
from .models import Question, Tag, Answer, QuestionVote, AnswerVote

class QuestionForm(forms.ModelForm):
    content = forms.CharField(max_length=10000)
    tags = forms.CharField(max_length=100)

    class Meta:
        model = Question
        fields = ("title", "content")

    def clean_tags(self):
        value = self.cleaned_data["tags"]
        names = []

        for part in value.split(","):
            name = part.strip()

            if not name:
                continue

            if len(name) > 35:
                raise forms.ValidationError(
                    "Каждый тег должен быть не длиннее 35 символов."
                )

            if name not in names:
                names.append(name)

        if not names:
            raise forms.ValidationError(
                "Укажите хотя бы один тег."
            )

        return names

    @transaction.atomic
    def save(self, *, user):
        question = super().save(commit=False)
        question.user = user
        question.save()

        for name in self.cleaned_data["tags"]:
            tag, created = Tag.objects.get_or_create(name=name)
            question.tags.add(tag)

        return question

class AnswerForm(forms.ModelForm):
    content = forms.CharField(max_length=5000, widget=forms.Textarea)
    class Meta:
        model = Answer
        fields = ("content",)

    @transaction.atomic
    def save(self, *, user, question):
        answer = super().save(commit=False)
        answer.user = user
        answer.question = question
        answer.save()

        return answer


class QuestionVoteForm(forms.Form):
    question_id = forms.ModelChoiceField(queryset=Question.objects.all())
    value = forms.TypedChoiceField(choices=((1, "Лайк"), (-1, "Дизлайк")), coerce=int)

    @transaction.atomic
    def save(self, *, user):
        question = Question.objects.select_for_update().get(pk=self.cleaned_data["question_id"].pk)
        value = self.cleaned_data["value"]
        vote, created = QuestionVote.objects.get_or_create(
            user=user, question=question, defaults={"value": value}
        )

        if not created and vote.value != value:
            vote.value = value
            vote.save(update_fields=["value"])

        rating = Question.objects.with_rating().get(pk=question.pk).rating
        return {"rating": rating, "vote": value}


class AnswerVoteForm(forms.Form):
    answer_id = forms.ModelChoiceField(queryset=Answer.objects.all())
    value = forms.TypedChoiceField(choices=((1, "Лайк"), (-1, "Дизлайк")), coerce=int)

    def __init__(self, *args, question, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["answer_id"].queryset = Answer.objects.filter(question=question)

    @transaction.atomic
    def save(self, *, user):
        answer = Answer.objects.select_for_update().get(pk=self.cleaned_data["answer_id"].pk)
        value = self.cleaned_data["value"]
        vote, created = AnswerVote.objects.get_or_create(
            user=user, answer=answer, defaults={"value": value}
        )

        if not created and vote.value != value:
            vote.value = value
            vote.save(update_fields=["value"])

        rating = Answer.objects.with_rating().get(pk=answer.pk).rating
        return {"rating": rating, "vote": value}


class CorrectAnswerForm(forms.Form):
    question_id = forms.ModelChoiceField(queryset=Question.objects.all())
    answer_id = forms.ModelChoiceField(queryset=Answer.objects.all())
    is_correct = forms.TypedChoiceField(
        choices=(("true", "Правильный"), ("false", "Не отмечен")),
        coerce=lambda value: value == "true",
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        question = cleaned_data.get("question_id")
        answer = cleaned_data.get("answer_id")

        if question and question.user_id != self.user.pk:
            raise forms.ValidationError(
                "Только автор вопроса может выбирать правильный ответ.", code="forbidden"
            )

        if question and answer and answer.question_id != question.pk:
            self.add_error("answer_id", "Ответ не относится к этому вопросу.")

        return cleaned_data

    @transaction.atomic
    def save(self):
        question = Question.objects.select_for_update().get(pk=self.cleaned_data["question_id"].pk)
        answer = self.cleaned_data["answer_id"]
        is_correct = self.cleaned_data["is_correct"]

        if is_correct:
            Answer.objects.filter(question=question, is_correct=True).exclude(pk=answer.pk).update(is_correct=False)

        Answer.objects.filter(pk=answer.pk, question=question).update(is_correct=is_correct)
        correct_answer_id = Answer.objects.filter(question=question, is_correct=True).values_list("pk", flat=True).first()
        return {"correct_answer_id": correct_answer_id}
