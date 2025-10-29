from __future__ import annotations

from typing import Optional

from django.http import HttpRequest

from .models import CaptchaLog


def log_captcha_event(
    *,
    request: HttpRequest,
    captcha_type: str,
    result: str,
    message: str = "",
    user_id: Optional[int] = None,
) -> None:
    ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
    CaptchaLog.objects.create(
        user_id=user_id,
        captcha_type=captcha_type,
        ip=ip,
        result=result,
        message=message,
    )
