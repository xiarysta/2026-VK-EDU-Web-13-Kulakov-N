from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Answer, Question, Tag


class PostingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="author")
        self.client.force_login(self.user)
        self.question = Question.objects.create(user=self.user, title="Вопрос", content="Описание")

    def test_question_creation_with_unique_tags(self):
        response = self.client.post(reverse("questions:ask"), {"title": "Новый вопрос", "content": "Описание", "tags": " Python, Django, Python "})
        question = Question.objects.get(title="Новый вопрос")
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(question.user, self.user)
        self.assertEqual(set(question.tags.values_list("name", flat=True)), {"Python", "Django"})

    def test_invalid_question_preserves_input_and_creates_nothing(self):
        response = self.client.post(reverse("questions:ask"), {"title": "Оставить", "content": "", "tags": "x" * 36})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Оставить"')
        self.assertTrue(response.context["form"].errors.get("content"))
        self.assertTrue(response.context["form"].errors.get("tags"))
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Tag.objects.count(), 0)

    def test_answer_redirects_to_page_and_anchor(self):
        Answer.objects.bulk_create([Answer(question=self.question, user=self.user, content="Старый") for _ in range(4)])
        response = self.client.post(self.question.get_absolute_url(), {"content": "Новый ответ"})
        answer = Answer.objects.get(content="Новый ответ")
        self.assertRedirects(response, f"{self.question.get_absolute_url()}?page=2#answer-{answer.pk}")
        self.assertContains(self.client.get(response.url), f'id="answer-{answer.pk}"')

    def test_invalid_answer_is_not_saved(self):
        response = self.client.post(self.question.get_absolute_url(), {"content": " "})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Answer.objects.count(), 0)

    def test_guests_cannot_post(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("questions:ask")).status_code, 302)
        self.assertEqual(self.client.post(self.question.get_absolute_url(), {"content": "spam"}).status_code, 302)
        self.assertEqual(Answer.objects.count(), 0)
