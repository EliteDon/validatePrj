from __future__ import annotations

from django.conf import settings
from django.db import models


class CaptchaType(models.Model):
    TYPE_CHOICES = [
        ("text", "数字字母混合"),
        ("puzzle", "拼图"),
        ("image_select", "图片选图"),
        ("email", "邮箱验证码"),
        ("sms", "短信验证码"),
        ("slider", "滑块"),
        ("audio", "语音验证码"),
    ]

    type_name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    config_json = models.JSONField(default=dict, blank=True)
    image_path = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "captcha_types"
        verbose_name = "Captcha Type"
        verbose_name_plural = "Captcha Types"

    def __str__(self) -> str:  # pragma: no cover
        return self.type_name

    def save(self, *args, **kwargs):
        if self.is_default:
            CaptchaType.objects.exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class SceneImage(models.Model):
    category = models.CharField(max_length=50)
    file_path = models.CharField(max_length=255)

    class Meta:
        db_table = "images"
        verbose_name = "Scene Image"
        verbose_name_plural = "Scene Images"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.category}:{self.file_path}"


class CaptchaLog(models.Model):
    RESULT_CHOICES = [
        ("success", "成功"),
        ("failed", "失败"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    captcha_type = models.CharField(max_length=50)
    ip = models.GenericIPAddressField(null=True, unpack_ipv4=True)
    access_time = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    message = models.TextField(blank=True)

    class Meta:
        db_table = "captcha_logs"
        verbose_name = "Captcha Log"
        verbose_name_plural = "Captcha Logs"
        ordering = ["-access_time"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.captcha_type} - {self.result}"


class LoginRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_records",
    )
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, unpack_ipv4=True)
    user_agent = models.CharField(max_length=200, blank=True)
    success = models.BooleanField(default=True)
    login_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "captcha_api_loginrecord"
        verbose_name = "Login Record"
        verbose_name_plural = "Login Records"
        ordering = ["-login_time"]

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        status = "成功" if self.success else "失败"
        return f"{self.username} - {status}"
