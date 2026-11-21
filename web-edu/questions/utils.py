from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import OuterRef, Subquery


def with_user_vote(queryset, user, kind):
    if not user.is_authenticated:
        return queryset
    from .models import AnswerVote, QuestionVote
    vote_model = QuestionVote if kind == "question" else AnswerVote
    return queryset.annotate(user_vote=Subquery(
        vote_model.objects.filter(user=user, **{f"{kind}_id": OuterRef("pk")}).values("value")[:1]
    ))

def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page) # создаем обьект, который знает все о разбиениях на страницы
    page_number = request.GET.get("page", "1") # берем номер страницы из GET-запроса, если номера нет, то считаем равным 1

    try:
        page = paginator.page(page_number) # берем страницу по ее номеру (если она существует и запрос правильный)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(1)

    page.page_numbers = paginator.get_elided_page_range(
        number=page.number,
        on_each_side=2,
        on_ends=1,
    )
    return page
