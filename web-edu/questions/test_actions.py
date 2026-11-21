from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Answer, AnswerVote, Question, QuestionVote


class ActionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner")
        self.other = User.objects.create_user(username="other")
        self.question = Question.objects.create(user=self.owner, title="Title", content="Text")
        self.answer = Answer.objects.create(user=self.other, question=self.question, content="Answer")
        self.client.force_login(self.owner)

    def test_votes_update_ratings_and_reject_duplicates(self):
        for kind, target, model in (("question", self.question, QuestionVote), ("answer", self.answer, AnswerVote)):
            url = reverse(f"questions:{kind}_vote")
            response = self.client.post(url, {"target": target.pk, "value": 1})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["rating"], 1)
            self.assertEqual(self.client.post(url, {"target": target.pk, "value": -1}).status_code, 409)
            self.assertEqual(model.objects.count(), 1)
            self.client.force_login(self.other)
            self.assertEqual(self.client.post(url, {"target": target.pk, "value": -1}).json()["rating"], 0)
            self.client.force_login(self.owner)

    def test_vote_rejects_invalid_parameters_and_method(self):
        url = reverse("questions:question_vote")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {"target": self.question.pk, "value": 10}).status_code, 400)
        self.assertEqual(self.client.post(url, {"target": 999999, "value": 1}).status_code, 400)
        self.assertEqual(QuestionVote.objects.count(), 0)

    def test_guests_cannot_use_api(self):
        self.client.logout()
        for name in ("question_vote", "answer_vote", "correct_answer"):
            self.assertEqual(self.client.post(reverse(f"questions:{name}"), {}).status_code, 401)

    def test_correct_answer_only_by_owner(self):
        url = reverse("questions:correct_answer")
        data = {"question": self.question.pk, "answer": self.answer.pk, "is_correct": "true"}
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, data).status_code, 403)
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_correct)
        self.client.force_login(self.owner)
        response = self.client.post(url, data)
        self.assertEqual(response.json()["correct_answer_id"], self.answer.pk)
        self.answer.refresh_from_db()
        self.assertTrue(self.answer.is_correct)
        data["is_correct"] = "false"
        self.assertIsNone(self.client.post(url, data).json()["correct_answer_id"])

    def test_correct_answer_rejects_wrong_question(self):
        other_question = Question.objects.create(user=self.owner, title="Other", content="Text")
        response = self.client.post(reverse("questions:correct_answer"), {"question": other_question.pk, "answer": self.answer.pk, "is_correct": "true"})
        self.assertEqual(response.status_code, 400)
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_correct)

    def test_selecting_another_answer_clears_previous(self):
        self.answer.is_correct = True
        self.answer.save()
        second = Answer.objects.create(user=self.other, question=self.question, content="Second")
        response = self.client.post(reverse("questions:correct_answer"), {"question": self.question.pk, "answer": second.pk, "is_correct": "true"})
        self.assertEqual(response.json()["correct_answer_id"], second.pk)
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_correct)

    def test_csrf_is_required_and_errors_are_json(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(reverse("questions:question_vote"), {"target": self.question.pk, "value": 1})
        self.assertEqual(response.status_code, 403)
        self.assertIn("CSRF", response.json()["error"])
        client.get(self.question.get_absolute_url())
        token = client.cookies["csrftoken"].value
        response = client.post(reverse("questions:question_vote"), {"target": self.question.pk, "value": 1}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_guest_buttons_and_correct_answer_permissions(self):
        self.client.logout()
        response = self.client.get(self.question.get_absolute_url())
        self.assertContains(response, 'disabled title="Войдите, чтобы голосовать"')
        self.assertNotContains(response, "data-correct-url=")
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.question.get_absolute_url()), "data-correct-url=")
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.question.get_absolute_url()), "data-correct-url=")

    def test_vote_buttons_stay_disabled_after_reload(self):
        QuestionVote.objects.create(user=self.owner, question=self.question, value=1)
        self.assertContains(self.client.get(self.question.get_absolute_url()), 'disabled title="Вы уже голосовали"', count=2)
