from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from .utils import paginate
from django.http import Http404
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.views import redirect_to_login
from .forms import QuestionForm, AnswerForm, QuestionVoteForm, AnswerVoteForm, CorrectAnswerForm
from .models import Question, Tag, Answer
from django.contrib.auth.decorators import login_required

def index(request):

    page = paginate(Question.objects.new(user=request.user), request, per_page=4)

    return render(request, "questions/index.html", context={"questions": page.object_list, "page_obj": page, "demo_authenticated": True})
    # для пагинации мы сначала получаем страницу с нужным номером, затем в контекст передаем список вопросов данной страницы и сам обьект, к-ый знает все обо всех вопросах на ней

def hot(request):

    page = paginate(Question.objects.hot(user=request.user), request, per_page=4)

    return render(request, "questions/hot.html", context={"hot_questions": page.object_list, "page_obj": page, "demo_authenticated": True})

def tag(request, tag_name):
    tag = Tag.objects.filter(name=tag_name).first()

    if tag is None:
        raise Http404("Тег не найден")

    page = paginate(Question.objects.by_tag(tag_name, user=request.user), request, per_page=4)
    
    return render(request, "questions/tag.html", context={
        "tag_questions": page.object_list,
        "page_obj": page,
        "tag": tag_name,
        "demo_authenticated": True,
    })

def question_detail(request, question_id):
    question = Question.objects.with_details(user=request.user).filter(pk=question_id).first()

    if question is None:
        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"error": "Вопрос не найден."}, status=404)
        raise Http404("Вопрос не найден")

    if "action" in request.POST or "action" in request.GET or request.headers.get("Accept") == "application/json":
        return question_action(request, question)

    page = paginate(Answer.objects.for_question(question_id, user=request.user), request, per_page=4)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(user=request.user, question=question)

            position = Answer.objects.filter(question=question).filter(
                Q(created_at__lt=answer.created_at)
                | Q(created_at=answer.created_at, pk__lte=answer.pk)
            ).count()
            answer_page = (position - 1) // page.paginator.per_page + 1
            return HttpResponseRedirect(
                f"{question.get_absolute_url()}?page={answer_page}#answer-{answer.pk}"
            )
    else:
        form = AnswerForm()

    return render(request, "questions/question_detail.html", context= {
        "question": question,
        "answers": page.object_list,
        "page_obj": page,
        "form": form,
    })

@login_required
def ask(request):
    if (request.method == 'POST'):
        form = QuestionForm(request.POST)

        if form.is_valid():
            question = form.save(user=request.user)
            return HttpResponseRedirect(question.get_absolute_url())

    else:
        form = QuestionForm()
    return render(request, "questions/ask.html", context={"form": form})


def question_action(request, question):
    if request.method != "POST":
        response = JsonResponse({"error": "Используйте метод POST."}, status=405)
        response["Allow"] = "POST"
        return response
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Войдите, чтобы выполнить действие."}, status=401)

    action = request.POST.get("action")
    data = request.POST.copy()
    data["question_id"] = question.pk

    if action == "vote_question":
        form = QuestionVoteForm(data)
    elif action == "vote_answer":
        form = AnswerVoteForm(data, question=question)
    elif action == "correct_answer":
        form = CorrectAnswerForm(data, user=request.user)
    else:
        return JsonResponse({"error": "Неизвестное действие."}, status=400)

    if form.is_valid():
        if action == "correct_answer":
            return JsonResponse(form.save())
        return JsonResponse(form.save(user=request.user))
    status = 403 if form.has_error("__all__", code="forbidden") else 400
    return JsonResponse({"errors": form.errors}, status=status)


def csrf_failure(request, reason=""):
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"error": "Ошибка CSRF. Обновите страницу и повторите действие."}, status=403)

    from django.views.csrf import csrf_failure as default_csrf_failure
    return default_csrf_failure(request, reason=reason)
