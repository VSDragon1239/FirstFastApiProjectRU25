from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser

    # 1) Какие поля выводить в списке
    list_display = (
        "nickname",
        'username',
        "email",
        "is_staff",
        "is_active",
    )
    # 2) Фильтры справа
    list_filter = (
        "is_staff",
        "is_active",
    )

    # 3) Какие поля редактировать на странице «Изменить пользователя»
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "nickname")}),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # 4) Какие поля нужны при создании нового пользователя
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "name", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    search_fields = ("username", "email", "nickname")
    ordering = ("email",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "description")
    search_fields = ("user__username",)
