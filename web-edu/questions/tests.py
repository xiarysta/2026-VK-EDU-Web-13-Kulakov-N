from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Question, Tag


class AskTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="question_author")
        self.client.force_login(self.user)
        self.url = reverse("questions:ask")

    def test_initial_form_has_fields_and_no_errors(self):
        response = self.client.get(self.url)
        for name in ("title", "content", "tags"):
            self.assertContains(response, f'name="{name}"')
        self.assertNotContains(response, 'role="alert"')
        self.assertNotContains(response, 'aria-invalid="true"')

    def test_invalid_tags_keep_all_entered_values(self):
        response = self.client.post(self.url, {"title": "Мой вопрос", "content": "Мой текст <test>", "tags": "x" * 36})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Мой вопрос"')
        self.assertContains(response, "Мой текст &lt;test&gt;")
        self.assertContains(response, 'value="' + "x" * 36 + '"')
        self.assertContains(response, "Каждый тег должен быть не длиннее 35 символов.")
        self.assertContains(response, 'id="tags-error"')
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Tag.objects.count(), 0)

    def test_commas_without_tags_are_rejected(self):
        response = self.client.post(self.url, {"title": "Вопрос", "content": "Текст", "tags": ", , ,"})
        self.assertContains(response, "Укажите хотя бы один тег.")
        self.assertEqual(Question.objects.count(), 0)

    def test_text_length_is_checked_on_server(self):
        response = self.client.post(self.url, {"title": "Вопрос", "content": "x" * 10001, "tags": "Python"})
        self.assertTrue(response.context["form"].errors.get("content"))
        self.assertEqual(Question.objects.count(), 0)

    def test_valid_question_is_saved_and_redirected(self):
        response = self.client.post(self.url, {"title": "Вопрос", "content": "Текст", "tags": "Python, Django, Python"})
        question = Question.objects.get()
        self.assertEqual(question.user, self.user)
        self.assertEqual(set(question.tags.values_list("name", flat=True)), {"Python", "Django"})
        self.assertRedirects(response, question.get_absolute_url())

class AnswerSubmissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="answer_author")
        self.client.force_login(self.user)
        self.question = Question.objects.create(user=self.user, title="Вопрос", content="Описание")
        self.url = self.question.get_absolute_url()

    def test_form_submits_content_and_saved_answer_is_visible(self):
        from .models import Answer
        self.assertContains(self.client.get(self.url), 'name="content"')
        response = self.client.post(self.url, {"content": "Проверочный ответ"}, follow=True)
        answer = Answer.objects.get(question=self.question)
        self.assertEqual(answer.user, self.user)
        self.assertContains(response, "Проверочный ответ")
        self.assertContains(response, f'id="answer-{answer.pk}"')

    def test_empty_answer_shows_validation_error(self):
        response = self.client.post(self.url, {"content": " "})
        self.assertContains(response, "Обязательное поле.")
        self.assertContains(response, 'aria-invalid="true"')

    def test_invalid_answer_preserves_entered_text(self):
        text = "x" * 5001
        response = self.client.post(self.url, {"content": text})
        self.assertContains(response, text)
        self.assertContains(response, 'id="answer-errors"')

    def test_new_answer_redirects_to_its_page_and_anchor(self):
        from .models import Answer

        for existing_count in (3, 4, 7, 8):
            with self.subTest(existing_count=existing_count):
                Answer.objects.filter(question=self.question).delete()
                Answer.objects.bulk_create([
                    Answer(user=self.user, question=self.question, content=f"Ответ {i}")
                    for i in range(existing_count)
                ])
                response = self.client.post(self.url + "?page=1", {"content": "Новый ответ"})
                answer = Answer.objects.latest("pk")
                expected_page = existing_count // 4 + 1
                self.assertRedirects(
                    response, f"{self.url}?page={expected_page}#answer-{answer.pk}"
                )
                page = self.client.get(response.url)
                self.assertContains(page, f'id="answer-{answer.pk}"')
                self.assertContains(page, "Новый ответ")

    def test_guest_sees_disabled_actions_and_no_answer_form(self):
        from .models import Answer

        Answer.objects.create(user=self.user, question=self.question, content="Ответ", is_correct=True)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertContains(response, 'disabled title="Войдите, чтобы задать вопрос"')
        self.assertContains(response, 'disabled title="Войдите, чтобы оценить вопрос"', count=2)
        self.assertContains(response, 'disabled title="Войдите, чтобы оценить ответ"', count=2)
        self.assertNotContains(response, 'name="content"')
        self.assertNotContains(response, 'type="checkbox"')
        self.assertContains(response, "✓ Правильный ответ")

    def test_only_question_author_sees_correct_answer_checkbox(self):
        from .models import Answer

        Answer.objects.create(user=self.user, question=self.question, content="Ответ")
        self.assertContains(self.client.get(self.url), 'type="checkbox"')
        other_user = get_user_model().objects.create_user(username="reader")
        self.client.force_login(other_user)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'type="checkbox"')
        self.assertNotContains(response, 'disabled title="Войдите')
        self.assertContains(response, 'name="content"')
