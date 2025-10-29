from __future__ import annotations

import json

from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from activity.services import log_captcha_event
from captcha_api.services import CaptchaVerifier
from captcha_backend.rate_limit import rate_limit

User = get_user_model()


def _parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit("register")
def register(request):
    payload = _parse_json(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "")

    if not username or not password:
        return JsonResponse({"success": False, "message": "用户名和密码必填"}, status=400)

    try:
        validate_password(password)
    except Exception as exc:
        if hasattr(exc, "messages"):
            message = " ".join(exc.messages)
        else:
            message = str(exc)
        return JsonResponse({"success": False, "message": message}, status=400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return JsonResponse({"success": False, "message": "用户名已存在"}, status=400)

    return JsonResponse({"success": True, "user": {"id": user.id, "username": user.username}})


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit("login")
def login_with_captcha(request):
    payload = _parse_json(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    captcha_token = payload.get("captcha_token")
    captcha_answer = payload.get("captcha_answer")

    if not all([username, password, captcha_token, captcha_answer]):
        return JsonResponse({"success": False, "message": "缺少登录信息或验证码"}, status=400)

    success, captcha_type, message = CaptchaVerifier.verify(captcha_token, captcha_answer)
    user_id = None
    if success:
        try:
            user_id = User.objects.only("id").get(username=username).id
        except User.DoesNotExist:
            user_id = None
    log_captcha_event(
        request=request,
        captcha_type=captcha_type,
        result="success" if success else "failed",
        message=message,
        user_id=user_id,
    )
    if not success:
        return JsonResponse({"success": False, "message": message}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"success": False, "message": "账号或密码错误"}, status=400)

    login(request, user)
    return JsonResponse({"success": True, "message": "登录成功"})
