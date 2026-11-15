from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

User = get_user_model()

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 1
    max_num = 1
    can_delete = False

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "name"]
    search_fields = ["name", "user__username", "user__email"]
    list_filter = ["user__is_active", "user__is_staff"]
    raw_id_fields = ["user"]
    list_select_related = ["user"]

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
