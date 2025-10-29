from __future__ import annotations

from django.conf import settings
from django.db import models


class CaptchaType(models.Model):
    type_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    config_json = models.JSONField(default=dict, blank=True)
    image_path = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "captcha_types"
        verbose_name = "Captcha Type"
        verbose_name_plural = "Captcha Types"

    def __str__(self) -> str:  # pragma: no cover
        return self.type_name


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
