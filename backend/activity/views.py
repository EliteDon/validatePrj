from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import CaptchaLog


def _admin_required(view_func):
    return user_passes_test(lambda user: user.is_staff, login_url=None)(view_func)



@csrf_exempt
@require_GET
@_admin_required
@login_required
def logs(request):
    queryset = (
        CaptchaLog.objects.select_related("user")
        .values("id", "captcha_type", "result", "ip", "access_time", "user__username", "message")
        .order_by("-access_time")[:200]
    )
    return JsonResponse({"success": True, "data": list(queryset)})


@csrf_exempt
@require_GET
@_admin_required
@login_required
def stats(request):
    total = CaptchaLog.objects.count()
    by_type = list(CaptchaLog.objects.values("captcha_type").annotate(total=Count("id")))
    success_ratio = (
        CaptchaLog.objects.filter(result="success").count(),
        CaptchaLog.objects.filter(result="failed").count(),
    )
    return JsonResponse(
        {
            "success": True,
            "data": {
                "total": total,
                "by_type": by_type,
                "success": success_ratio[0],
                "failed": success_ratio[1],
            },
        }
    )
