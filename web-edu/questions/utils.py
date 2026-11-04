from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

def paginate(objects_list, request, per_page=10):
  paginator = Paginator(objects_list, per_page) # создаем обьект, который знает все о разбиениях на страницы
  page_number = request.GET.get("page", "1") # берем номер страницы из GET-запроса, если номера нет, то считаем равным 1

  try:
    page = paginator.page(page_number) # берем страницу по ее номеру (если она существует и запрос правильный)
  except PageNotAnInteger:
    page = paginator.page(1)
  except EmptyPage:
    page = paginator.page(1)

  return page