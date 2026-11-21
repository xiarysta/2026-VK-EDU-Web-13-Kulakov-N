from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Question, Answer, QuestionVote, AnswerVote, Tag


class ActionTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="author")
        self.reader = get_user_model().objects.create_user(username="reader")
        self.question = Question.objects.create(user=self.author, title="Вопрос", content="Текст")
        self.answer = Answer.objects.create(user=self.reader, question=self.question, content="Ответ")
        self.other_answer = Answer.objects.create(user=self.author, question=self.question, content="Другой ответ")
        self.client.force_login(self.author)
        self.question_url = "vote_question"
        self.answer_url = "vote_answer"
        self.correct_url = "correct_answer"

    def post(self, action, data, client=None, url=None, **kwargs):
        return (client or self.client).post(
            url or self.question.get_absolute_url(),
            {**data, "action": action}, HTTP_ACCEPT="application/json", **kwargs
        )

    def correct_data(self, answer=None, is_correct="true"):
        return {
            "question_id": self.question.pk,
            "answer_id": (answer or self.answer).pk,
            "is_correct": is_correct,
        }

    def test_votes_create_switch_and_ignore_repeated_votes(self):
        for url, key, target, model in (
            (self.question_url, "question_id", self.question, QuestionVote),
            (self.answer_url, "answer_id", self.answer, AnswerVote),
        ):
            with self.subTest(url=url):
                for value, expected in ((1, 1), (1, 1), (-1, -1), (-1, -1), (1, 1), (1, 1)):
                    response = self.post(url, {key: target.pk, "value": value})
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), {"rating": expected, "vote": expected})
                    self.assertEqual(model.objects.filter(user=self.author).count(), int(expected != 0))

    def test_rating_includes_other_users_and_votes_are_independent(self):
        QuestionVote.objects.create(user=self.reader, question=self.question, value=1)
        AnswerVote.objects.create(user=self.reader, answer=self.answer, value=1)
        for url, data in (
            (self.question_url, {"question_id": self.question.pk, "value": -1}),
            (self.answer_url, {"answer_id": self.answer.pk, "value": -1}),
        ):
            response = self.post(url, data)
            self.assertEqual(response.json(), {"rating": 0, "vote": -1})
        self.assertEqual(QuestionVote.objects.get(user=self.reader).value, 1)
        self.assertEqual(AnswerVote.objects.get(user=self.reader).value, 1)

    def test_vote_rejects_invalid_values_and_ids(self):
        for url, key, target in (
            (self.question_url, "question_id", self.question),
            (self.answer_url, "answer_id", self.answer),
        ):
            invalid_data = [{}, {key: target.pk, "value": 0}, {key: target.pk, "value": "bad"}]
            if key == "answer_id":
                invalid_data += [{key: "bad", "value": 1}, {key: 999999, "value": 1}]
            for data in invalid_data:
                with self.subTest(url=url, data=data):
                    response = self.post(url, data)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("errors", response.json())
        self.assertFalse(QuestionVote.objects.exists())
        self.assertFalse(AnswerVote.objects.exists())

    def test_correct_answer_can_be_selected_replaced_and_unselected(self):
        for answer, state, expected_id in (
            (self.answer, "true", self.answer.pk),
            (self.answer, "true", self.answer.pk),
            (self.other_answer, "true", self.other_answer.pk),
            (self.answer, "false", self.other_answer.pk),
            (self.other_answer, "false", None),
            (self.other_answer, "false", None),
        ):
            response = self.post(self.correct_url, self.correct_data(answer, state))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"correct_answer_id": expected_id})
            self.assertEqual(
                list(Answer.objects.filter(question=self.question, is_correct=True).values_list("pk", flat=True)),
                [expected_id] if expected_id else [],
            )

    def test_only_question_author_can_select_correct_answer(self):
        self.client.force_login(self.reader)
        response = self.post(self.correct_url, self.correct_data())
        self.assertEqual(response.status_code, 403)
        self.assertIn("Только автор", response.json()["errors"]["__all__"][0])
        self.assertFalse(Answer.objects.filter(is_correct=True).exists())

    def test_correct_answer_must_belong_to_question(self):
        other_question = Question.objects.create(user=self.author, title="Другой вопрос", content="Текст")
        data = self.correct_data()
        data["question_id"] = other_question.pk
        response = self.post(self.correct_url, data, url=other_question.get_absolute_url())
        self.assertEqual(response.status_code, 400)
        self.assertIn("answer_id", response.json()["errors"])
        self.assertFalse(Answer.objects.filter(is_correct=True).exists())

    def test_invalid_correct_answer_data_does_not_change_existing_mark(self):
        self.answer.is_correct = True
        self.answer.save()
        for changes in ({"answer_id": 999999},
                        {"answer_id": "bad"}, {"is_correct": "yes"}, {"is_correct": ""}):
            response = self.post(self.correct_url, {**self.correct_data(), **changes})
            self.assertEqual(response.status_code, 400)
            self.assertIn("errors", response.json())
        self.answer.refresh_from_db()
        self.assertTrue(self.answer.is_correct)

    def test_anonymous_actions_return_json_without_changing_data(self):
        self.client.logout()
        for url, data in (
            (self.question_url, {"question_id": self.question.pk, "value": 1}),
            (self.answer_url, {"answer_id": self.answer.pk, "value": 1}),
            (self.correct_url, self.correct_data()),
        ):
            response = self.post(url, data)
            self.assertEqual(response.status_code, 401)
            self.assertIn("error", response.json())
        self.assertFalse(QuestionVote.objects.exists())
        self.assertFalse(AnswerVote.objects.exists())
        self.assertFalse(Answer.objects.filter(is_correct=True).exists())

    def test_wrong_methods_return_json_and_allow_header(self):
        for url in (self.question_url, self.answer_url, self.correct_url):
            for method in ("get", "put", "delete"):
                response = getattr(self.client, method)(
                    self.question.get_absolute_url() + "?action=" + url,
                    HTTP_ACCEPT="application/json",
                )
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "POST")
                self.assertIn("error", response.json())

    def test_csrf_is_required_and_valid_token_allows_actions(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.author)
        for url, data in (
            (self.question_url, {"question_id": self.question.pk, "value": 1}),
            (self.answer_url, {"answer_id": self.answer.pk, "value": 1}),
            (self.correct_url, self.correct_data()),
        ):
            response = self.post(url, data, client=client)
            self.assertEqual(response.status_code, 403)
            self.assertIn("CSRF", response.json()["error"])
            client.get(self.question.get_absolute_url())
            response = self.post(url, data, client=client, HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
            self.assertEqual(response.status_code, 200)

    def test_selected_vote_survives_page_reload(self):
        QuestionVote.objects.create(user=self.author, question=self.question, value=1)
        AnswerVote.objects.create(user=self.author, answer=self.answer, value=-1)
        tag = Tag.objects.create(name="Python")
        self.question.tags.add(tag)
        for url in (reverse("questions:index"), reverse("questions:hot"),
                    reverse("questions:tag_detail", args=[tag.name]), self.question.get_absolute_url()):
            response = self.client.get(url)
            self.assertContains(response, 'data-value="1" class="vote-active" aria-pressed="true"')
            self.assertContains(response, 'disabled title="Вы уже поставили эту оценку"')
        self.assertContains(
            self.client.get(self.question.get_absolute_url()),
            'data-value="-1" class="vote-active" aria-pressed="true"',
        )
        self.client.force_login(self.reader)
        self.assertNotContains(self.client.get(self.question.get_absolute_url()), 'class="vote-active"')

    def test_unknown_or_missing_action_returns_json_without_creating_answer(self):
        for data in ({"action": "unknown"}, {}):
            response = self.client.post(
                self.question.get_absolute_url(), data, HTTP_ACCEPT="application/json"
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json())
        self.assertEqual(Answer.objects.count(), 2)

    def test_answer_vote_cannot_target_another_question(self):
        other_question = Question.objects.create(user=self.author, title="Другой вопрос", content="Текст")
        response = self.post("vote_answer", {"answer_id": self.answer.pk, "value": 1},
                             url=other_question.get_absolute_url())
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AnswerVote.objects.exists())

    def test_question_id_in_body_cannot_override_url(self):
        other_question = Question.objects.create(user=self.reader, title="Другой вопрос", content="Текст")
        response = self.post("vote_question", {"question_id": other_question.pk, "value": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuestionVote.objects.get().question_id, self.question.pk)

    def test_missing_question_returns_json_for_ajax(self):
        response = self.post("vote_question", {"value": 1}, url=reverse("questions:question_detail", args=[999999]))
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())
