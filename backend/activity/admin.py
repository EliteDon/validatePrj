from django.contrib import admin

from .models import CaptchaLog, CaptchaType, SceneImage


@admin.register(CaptchaType)
class CaptchaTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name", "description")
    search_fields = ("type_name",)


@admin.register(SceneImage)
class SceneImageAdmin(admin.ModelAdmin):
    list_display = ("category", "file_path")
    list_filter = ("category",)


@admin.register(CaptchaLog)
class CaptchaLogAdmin(admin.ModelAdmin):
    list_display = ("captcha_type", "user", "ip", "result", "access_time")
    list_filter = ("captcha_type", "result")
    search_fields = ("user__username", "captcha_type", "ip")
    readonly_fields = ("access_time",)
