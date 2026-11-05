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

    return render(request, "questions/hot.html", context={"hot_questions": page.object_list, "page_obj": page})

def tag(request, tag_name):
    TAG_QUESTION_LIST = [ question for question in QUESTION_LIST if tag_name in question["tags"] ]

    page = paginate(TAG_QUESTION_LIST, request, per_page=4)
    
    return render(request, "questions/tag.html", context={
        "tag_questions": page.object_list,
        "page_obj": page,
        "tag": tag_name,
    })