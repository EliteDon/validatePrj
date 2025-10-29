from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_in_seconds: int


def _cache_key(prefix: str, request: HttpRequest) -> str:
    client_ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR", "unknown")
    return f"rate-limit:{prefix}:{client_ip}"


def rate_limit(prefix: str) -> Callable[[Callable[..., JsonResponse]], Callable[..., JsonResponse]]:
    window = int(settings.RATE_LIMIT_WINDOW.total_seconds())
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    def decorator(view_func: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
        def wrapped(request: HttpRequest, *args, **kwargs):
            key = _cache_key(prefix, request)
            now = timezone.now()
            record: Optional[dict] = cache.get(key)

            if record and record["expires_at"] > now:
                count = record["count"]
                if count >= max_requests:
                    reset_in = int((record["expires_at"] - now).total_seconds())
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Too many requests. Please wait before retrying.",
                            "reset_in": reset_in,
                        },
                        status=429,
                    )
                cache.set(
                    key,
                    {"count": count + 1, "expires_at": record["expires_at"]},
                    timeout=reset_timeout(record["expires_at"], now),
                )
            else:
                expires_at = now + settings.RATE_LIMIT_WINDOW
                cache.set(key, {"count": 1, "expires_at": expires_at}, timeout=window)

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def reset_timeout(expires_at, now):
    return max(1, int((expires_at - now).total_seconds()))
