from django.shortcuts import render
from .utils import paginate
from django.http import Http404
from .models import Question, Tag, Answer

def index(request):

    page = paginate(Question.objects.new(), request, per_page=4)

    return render(request, "questions/index.html", context={"questions": page.object_list, "page_obj": page, "demo_authenticated": True})
    # для пагинации мы сначала получаем страницу с нужным номером, затем в контекст передаем список вопросов данной страницы и сам обьект, к-ый знает все обо всех вопросах на ней

def hot(request):

    page = paginate(Question.objects.hot(), request, per_page=4)

    return render(request, "questions/hot.html", context={"hot_questions": page.object_list, "page_obj": page, "demo_authenticated": True})

def tag(request, tag_name):
    tag = Tag.objects.filter(name=tag_name).first()

    if tag is None:
        raise Http404("Тег не найден")

    page = paginate(Question.objects.by_tag(tag_name), request, per_page=4)
    
    return render(request, "questions/tag.html", context={
        "tag_questions": page.object_list,
        "page_obj": page,
        "tag": tag_name,
        "demo_authenticated": True,
    })

def question_detail(request, question_id):
    question = Question.objects.with_details().filter(pk=question_id).first()

    if question is None:
        raise Http404("Вопрос не найден")

    page = paginate(Answer.objects.for_question(question_id), request, per_page=4)

    return render(request, "questions/question_detail.html", context= {
        "question": question,
        "answers": page.object_list,
        "page_obj": page,
        "demo_authenticated": True,
    })

def ask(request):
    return render(request, "questions/ask.html", context={"demo_authenticated": False})
