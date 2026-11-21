from uuid import uuid4

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from users.models import UserProfile
from questions.models import Tag, Question, QuestionTag, Answer, QuestionVote, AnswerVote

class Command(BaseCommand):
    help = "Наполнение БД тестовыми данными"

    def add_arguments(self, parser):            # принимаем аргумента типа int: .../manage.py fill_db 10 <--
        parser.add_argument("ratio", type=int)

    def handle(self, *args, **options):         # запускается при вызове комманды fill_db
        ratio = options["ratio"]

        if ratio < 2:
            raise CommandError("Используй ratio >= 2")

        User = get_user_model()
        fake = Faker("ru_RU")

        users = []

        for i in range(ratio):
            user = User(
                username=f"test_{uuid4().hex}",
                first_name=fake.first_name(),
                last_name = fake.last_name(),
            )

            user.set_unusable_password()
            users.append(user)

        User.objects.bulk_create(users, batch_size=1000)

        profiles = []

        for user in users:
            profile = UserProfile(
                user=user,
                name=user.first_name,
            )

            profiles.append(profile)

        UserProfile.objects.bulk_create(profiles, batch_size=1000)

        tags = []

        for i in range(ratio):
            tag = Tag(
                name = f"{fake.word()[:10]}_{uuid4().hex[:20]}",
            )

            tags.append(tag)

        Tag.objects.bulk_create(tags, batch_size=1000)

        questions = []

        for i in range(ratio * 10):
            question = Question(
                user=random.choice(users),
                title=fake.sentence(nb_words=6)[:150],
                content=fake.paragraph(nb_sentences=5),
            )

            questions.append(question)

        Question.objects.bulk_create(questions, batch_size=1000)

        question_tags = []

        for question in questions:
            selected_tags = random.sample(
                tags,
                k=min(3, len(tags)),
            )

            for tag in selected_tags:
                question_tag = QuestionTag(
                    question=question,
                    tag=tag
                )

                question_tags.append(question_tag)

        QuestionTag.objects.bulk_create(question_tags, batch_size=1000)

        answers = []

        for i in range(ratio * 100):
            answer = Answer(
                user=random.choice(users),
                question=random.choice(questions),
                content=fake.paragraph(nb_sentences=4),
            )

            answers.append(answer)

            if len(answers) >= 1000:
                Answer.objects.bulk_create(answers, batch_size=1000)
                answers.clear()

        if answers:
            Answer.objects.bulk_create(answers, batch_size=1000)

        question_votes = []
        question_votes_count = 0

        for question in questions:
            voters = random.sample(users, k=min(10, len(users)))

            for user in voters:
                question_vote = QuestionVote(
                    user=user,
                    question=question,
                    value=random.choice([-1, 1])
                )

                question_votes.append(question_vote)
                question_votes_count += 1

                if len(question_votes) >= 1000:
                    QuestionVote.objects.bulk_create(question_votes, batch_size=1000)
                    question_votes.clear()

        if question_votes:
            QuestionVote.objects.bulk_create(question_votes, batch_size=1000)

        votes_needed = ratio * 200 - question_votes_count
        answer_votes = []
        answer_votes_count = 0

        saved_answers = Answer.objects.filter(user__in=users) # чтобы выбрать только новые ответы у новых пользователей

        for answer in saved_answers.iterator(chunk_size=1000): # читаем порциями по 1000, а не загружаем все ответы сразу
            remaining = votes_needed - answer_votes_count

            if remaining == 0:
                break

            votes = random.sample(users, k=min(10, len(users), remaining))

            for user in votes:
                answer_vote = AnswerVote(
                    user=user,
                    answer=answer,
                    value=random.choice([-1, 1])
                )

                answer_votes.append(answer_vote)
                answer_votes_count += 1

                if len(answer_votes) >= 1000:
                    AnswerVote.objects.bulk_create(answer_votes, batch_size=1000)
                    answer_votes.clear()

        if answer_votes:
            AnswerVote.objects.bulk_create(answer_votes, batch_size=1000)
