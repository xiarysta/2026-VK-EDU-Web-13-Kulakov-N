from django import forms
from django.db import transaction

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(max_length=100, label="Теги", help_text="Укажите теги через запятую. Каждый тег — до 35 символов.")
    content = forms.CharField(max_length=10000, widget=forms.Textarea(attrs={"rows": 10}), label="Текст")

    class Meta:
        model = Question
        fields = ("title", "content")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user

    def clean_tags(self):
        names = list(dict.fromkeys(name.strip() for name in self.cleaned_data["tags"].split(",") if name.strip()))
        if not names:
            raise forms.ValidationError("Укажите хотя бы один тег.")
        if any(len(name) > 35 for name in names):
            raise forms.ValidationError("Тег не должен быть длиннее 35 символов.")
        return names

    @transaction.atomic
    def save(self, commit=True):
        question = super().save(commit=commit)
        if commit:
            question.tags.set([Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data["tags"]])
        return question


class AnswerForm(forms.ModelForm):
    content = forms.CharField(max_length=5000, widget=forms.Textarea(attrs={"rows": 4}), label="Ваш ответ")

    class Meta:
        model = Answer
        fields = ("content",)

    def __init__(self, *args, user, question, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.question = question

class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=((1, "Лайк"), (-1, "Дизлайк")), coerce=int)

    def __init__(self, *args, user, kind, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import AnswerVote, QuestionVote
        self.user = user
        self.kind = kind
        self.vote_model = QuestionVote if kind == "question" else AnswerVote
        model = Question if kind == "question" else Answer
        self.fields["target"] = forms.ModelChoiceField(queryset=model.objects.all())

    def clean(self):
        data = super().clean()
        target = data.get("target")
        if target and self.vote_model.objects.filter(user=self.user, **{self.kind: target}).exists():
            raise forms.ValidationError("Вы уже голосовали.", code="duplicate")
        return data

    @transaction.atomic
    def save(self):
        from django.db.models import Sum
        target = self.cleaned_data["target"]
        vote, created = self.vote_model.objects.get_or_create(
            user=self.user, **{self.kind: target}, defaults={"value": self.cleaned_data["value"]}
        )
        if not created:
            raise forms.ValidationError("Вы уже голосовали.", code="duplicate")
        return self.vote_model.objects.filter(**{self.kind: target}).aggregate(total=Sum("value"))["total"] or 0


class CorrectAnswerForm(forms.Form):
    question = forms.ModelChoiceField(queryset=Question.objects.all())
    answer = forms.ModelChoiceField(queryset=Answer.objects.all())
    is_correct = forms.TypedChoiceField(choices=(("true", "Да"), ("false", "Нет")), coerce=lambda value: value == "true")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        data = super().clean()
        question, answer = data.get("question"), data.get("answer")
        if question and question.user_id != self.user.pk:
            raise forms.ValidationError("Только автор вопроса может выбирать правильный ответ.", code="forbidden")
        if question and answer and answer.question_id != question.pk:
            raise forms.ValidationError("Ответ не относится к этому вопросу.")
        return data

    @transaction.atomic
    def save(self):
        question = self.cleaned_data["question"]
        Question.objects.select_for_update().get(pk=question.pk)
        answer = self.cleaned_data["answer"]
        is_correct = self.cleaned_data["is_correct"]
        if is_correct:
            Answer.objects.filter(question=question, is_correct=True).exclude(pk=answer.pk).update(is_correct=False)
        Answer.objects.filter(pk=answer.pk).update(is_correct=is_correct)
        return Answer.objects.filter(question=question, is_correct=True).values_list("pk", flat=True).first()
