from django.shortcuts import render
from .utils import paginate, with_user_vote
from django.http import Http404
from .models import Question, Tag, Answer
from .forms import QuestionForm, AnswerForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
from django.http import HttpResponseRedirect
from django.db.models import Q

def index(request):

    page = paginate(with_user_vote(Question.objects.new(), request.user, "question"), request, per_page=4)

    return render(request, "questions/index.html", context={"questions": page.object_list, "page_obj": page, "demo_authenticated": True})
    # для пагинации мы сначала получаем страницу с нужным номером, затем в контекст передаем список вопросов данной страницы и сам обьект, к-ый знает все обо всех вопросах на ней

def hot(request):

    page = paginate(with_user_vote(Question.objects.hot(), request.user, "question"), request, per_page=4)

    return render(request, "questions/hot.html", context={"hot_questions": page.object_list, "page_obj": page, "demo_authenticated": True})

def tag(request, tag_name):
    tag = Tag.objects.filter(name=tag_name).first()

    if tag is None:
        raise Http404("Тег не найден")

    page = paginate(with_user_vote(Question.objects.by_tag(tag_name), request.user, "question"), request, per_page=4)

    return render(request, "questions/tag.html", context={
        "tag_questions": page.object_list,
        "page_obj": page,
        "tag": tag_name,
        "demo_authenticated": True,
    })

def question_detail(request, question_id):
    question = with_user_vote(Question.objects.with_details(), request.user, "question").filter(pk=question_id).first()

    if question is None:
        raise Http404("Вопрос не найден")

    if request.method == "POST" and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
    form = AnswerForm(
        request.POST if request.method == "POST" else None,
        user=request.user if request.user.is_authenticated else None,
        question=question,
    )
    if request.method == "POST" and form.is_valid():
        answer = form.save()
        position = Answer.objects.filter(question=question).filter(
            Q(created_at__lt=answer.created_at) | Q(created_at=answer.created_at, pk__lte=answer.pk)
        ).count()
        return HttpResponseRedirect(f"{question.get_absolute_url()}?page={(position - 1) // 4 + 1}#answer-{answer.pk}")

    page = paginate(with_user_vote(Answer.objects.for_question(question_id), request.user, "answer"), request, per_page=4)

    return render(request, "questions/question_detail.html", context= {
        "question": question,
        "answers": page.object_list,
        "page_obj": page,
        "form": form,
        "demo_authenticated": True,
    })

@login_required
def ask(request):
    form = QuestionForm(request.POST if request.method == "POST" else None, user=request.user)
    if request.method == "POST" and form.is_valid():
        question = form.save()
        return HttpResponseRedirect(question.get_absolute_url())
    return render(request, "questions/ask.html", {"form": form})
