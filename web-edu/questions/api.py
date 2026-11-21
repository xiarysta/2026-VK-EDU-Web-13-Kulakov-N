from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.csrf import csrf_failure

from .forms import CorrectAnswerForm, VoteForm


def form_response(form):
    if form.is_valid():
        try:
            result = form.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            key = "rating" if isinstance(form, VoteForm) else "correct_answer_id"
            return JsonResponse({key: result})
    codes = {error.code for errors in form.errors.as_data().values() for error in errors}
    status = 403 if "forbidden" in codes else 409 if "duplicate" in codes else 400
    return JsonResponse({"errors": form.errors.get_json_data()}, status=status)


def api_guard(request):
    if request.method != "POST":
        response = JsonResponse({"error": "Используйте POST."}, status=405)
        response["Allow"] = "POST"
        return response
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Войдите, чтобы выполнить действие."}, status=401)
    return None


def question_vote(request):
    return vote(request, "question")


def answer_vote(request):
    return vote(request, "answer")


def vote(request, kind):
    failure = api_guard(request)
    if failure is not None:
        return failure
    return form_response(VoteForm(request.POST, user=request.user, kind=kind))


def correct_answer(request):
    failure = api_guard(request)
    if failure is not None:
        return failure
    return form_response(CorrectAnswerForm(request.POST, user=request.user))


def csrf_error(request, reason=""):
    if request.path.startswith("/api/"):
        return JsonResponse({"error": "Проверка CSRF не пройдена. Обновите страницу и повторите действие."}, status=403)
    return csrf_failure(request, reason=reason)
