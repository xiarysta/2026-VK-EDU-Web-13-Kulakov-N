from django.shortcuts import render
from .utils import paginate
from .data import QUESTION_LIST, ANSWER_LIST
from django.http import Http404

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

def question_detail(request, question_id):
    question = None

    for item in QUESTION_LIST:
        if item["id"] == question_id:
            question = item
            break

    if question is None:
        raise Http404("Вопрос не найден")

    QUESTION_ANSWERS = [ answer for answer in ANSWER_LIST if answer["question_id"] == question_id ] 

    page = paginate(QUESTION_ANSWERS, request, per_page=4)

    return render(request, "questions/question_detail.html", context= {
        "question": question,
        "answers": page.object_list,
        "page_obj": page,
    })