from django.shortcuts import render
from .utils import paginate
from .data import QUESTION_LIST

def index(request):

    page = paginate(QUESTION_LIST, request, per_page=4)

    return render(request, "questions/index.html", context={"questions": page.object_list, "page_obj": page})
    # для пагинации мы сначала получаем страницу с нужным номером, затем в контекст передаем список вопросов данной страницы и сам обьект, к-ый знает все обо всех вопросах на ней

def hot(request):
    HOT_QUESTION_LIST = sorted(QUESTION_LIST, key=lambda question: question["rating"], reverse=True)

    page = paginate(HOT_QUESTION_LIST, request, per_page=4)
    print(request)

    return render(request, "questions/hot.html", context={"hot_questions": page.object_list, "page_obj": page})