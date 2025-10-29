from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "register_time")
    readonly_fields = ("register_time",)
    fieldsets = UserAdmin.fieldsets + (("Meta", {"fields": ("register_time",)}),)
