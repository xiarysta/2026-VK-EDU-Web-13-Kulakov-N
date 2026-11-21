from django.contrib import admin
from .models import Question, QuestionVote, QuestionTag, Answer, AnswerVote, Tag
from django.db.models import Exists, OuterRef


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ["user"]

class QuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created_at"]
    search_fields = ["title", "user__username"]
    raw_id_fields = ["user"]
    list_filter = ["created_at"]
    list_select_related = ["user"]
    inlines = [AnswerInline]

class TagUsageFilter(admin.SimpleListFilter):
    title = "Использование тега"
    parameter_name = "usage"

    def lookups(self, request, model_admin):
        return [
            ("used", "Используется"),
            ("unused", "Не используется"),
        ]

    def queryset(self, request, queryset):
        tag_links = QuestionTag.objects.filter(tag_id=OuterRef("pk"))

        if self.value() == "used":
            return queryset.filter(Exists(tag_links))

        if self.value() == "unused":
            return queryset.filter(~Exists(tag_links))
        
        return queryset
    
class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    list_filter = [TagUsageFilter]

class AnswerAdmin(admin.ModelAdmin):
    list_display = ["id", "content", "user", "question", "is_correct", "created_at"]
    search_fields = ["content", "user__username", "question__title"]
    search_help_text = "Поиск по тексту ответа, логину автора и заголовку вопроса."
    raw_id_fields = ["question", "user"]
    list_filter = ["is_correct", "created_at"]
    list_select_related = ["question", "user"]

class QuestionTagAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "tag"]
    search_fields = ["question__title", "tag__name"]
    list_filter = [("question__created_at", admin.DateFieldListFilter)]
    raw_id_fields = ["question", "tag"]
    list_select_related = ["question", "tag"]

class QuestionVoteAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "question", "value"]
    raw_id_fields = ["user", "question"]
    search_fields = ["user__username", "question__title"]
    list_filter = ["value"]
    list_select_related = ["question", "user"]

class AnswerVoteAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "answer", "value"]
    raw_id_fields = ["user", "answer"]
    search_fields = ["user__username", "answer__content"]
    list_filter = ["value"]
    list_select_related = ["answer", "user"]

admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionVote, QuestionVoteAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AnswerVote, AnswerVoteAdmin)
admin.site.register(Tag, TagAdmin)

