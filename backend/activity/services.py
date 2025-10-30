from __future__ import annotations

from typing import Optional

from django.http import HttpRequest
from django.utils import timezone

from .models import CaptchaLog, LoginRecord


def get_client_ip(request: HttpRequest) -> str | None:
    """Return the best-guess client IP address for a request."""

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    if ip in {"", "unknown", None}:
        return None
    return ip


def log_captcha_event(
    *,
    request: HttpRequest,
    captcha_type: str,
    result: str,
    message: str = "",
    user_id: Optional[int] = None,
) -> None:
    ip = get_client_ip(request)
    CaptchaLog.objects.create(
        user_id=user_id,
        captcha_type=captcha_type,
        ip=ip,
        result=result,
        message=message,
    )


def log_login_event(
    *,
    request: HttpRequest,
    username: str,
    success: bool,
    user_id: Optional[int] = None,
) -> None:
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")[:200]
    LoginRecord.objects.create(
        user_id=user_id,
        username=username,
        ip_address=ip,
        user_agent=user_agent,
        success=success,
        login_time=timezone.now(),
    )
