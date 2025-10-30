from __future__ import annotations

import json
import re

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from activity.services import log_captcha_event, log_login_event
from captcha_api.services import (
    CaptchaVerifier,
    VerificationCodeService,
    get_default_captcha_type,
)
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
    captcha_type = payload.get("captcha_type") or get_default_captcha_type().type_name

    if not all([username, password]):
        return JsonResponse({"success": False, "message": "用户名和密码必填"}, status=400)

    captcha_verified = False
    message = ""
    user_lookup = None
    try:
        user_lookup = User.objects.only("id").get(username=username)
    except User.DoesNotExist:
        user_lookup = None

    if captcha_type in {"email", "sms"}:
        code = payload.get("code") or payload.get("captcha_answer")
        contact_key = "email" if captcha_type == "email" else "phone"
        target_value = payload.get(contact_key)
        if not target_value or not code:
            return JsonResponse({"success": False, "message": "验证码信息不完整"}, status=400)

        if captcha_type == "email":
            captcha_verified = VerificationCodeService.validate_email_code(target_value, code)
        else:
            captcha_verified = VerificationCodeService.validate_sms_code(target_value, code)
        message = "验证成功" if captcha_verified else "验证码错误"
        log_captcha_event(
            request=request,
            captcha_type=captcha_type,
            result="success" if captcha_verified else "failed",
            message=message,
            user_id=user_lookup.id if user_lookup else None,
        )
    else:
        captcha_token = payload.get("captcha_token")
        captcha_answer = payload.get("captcha_answer")

        if not all([captcha_token, captcha_answer]):
            return JsonResponse({"success": False, "message": "缺少验证码信息"}, status=400)

        captcha_verified, captcha_type, message = CaptchaVerifier.verify(captcha_token, captcha_answer)
        log_captcha_event(
            request=request,
            captcha_type=captcha_type,
            result="success" if captcha_verified else "failed",
            message=message,
            user_id=user_lookup.id if user_lookup else None,
        )

    if not captcha_verified:
        return JsonResponse({"success": False, "message": message or "验证码错误"}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        log_login_event(
            request=request,
            username=username,
            success=False,
            user_id=user_lookup.id if user_lookup else None,
        )
        return JsonResponse({"success": False, "message": "账号或密码错误"}, status=400)

    login(request, user)
    log_login_event(
        request=request,
        username=username,
        success=True,
        user_id=user.id,
    )
    redirect_url = "/admin-dashboard" if user.is_staff else "/success"
    return JsonResponse(
        {
            "success": True,
            "message": "登录成功",
            "is_staff": user.is_staff,
            "redirect": redirect_url,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit("email-code")
def send_email_code(request):
    payload = _parse_json(request)
    email = payload.get("email", "").strip()
    if not email:
        return JsonResponse({"success": False, "message": "邮箱地址必填"}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"success": False, "message": "邮箱格式不正确"}, status=400)

    code = VerificationCodeService.create_email_code(email)
    mail = EmailMessage(
        subject="验证码登录验证",
        body=f"您的验证码是 {code} ，5 分钟内有效。",
        to=[email],
    )
    mail.send(fail_silently=not settings.DEBUG)

    response_payload = {"success": True, "message": "验证码已发送"}
    if settings.DEBUG:
        response_payload["debug_code"] = code
    return JsonResponse(response_payload)


PHONE_REGEX = re.compile(r"^\+?\d{6,15}$")


@csrf_exempt
@require_http_methods(["POST"])
@rate_limit("sms-code")
def send_sms_code(request):
    payload = _parse_json(request)
    phone = (payload.get("phone") or "").strip()
    if not phone:
        return JsonResponse({"success": False, "message": "手机号必填"}, status=400)
    if not PHONE_REGEX.match(phone):
        return JsonResponse({"success": False, "message": "手机号格式无效"}, status=400)

    code = VerificationCodeService.create_sms_code(phone)

    response_payload = {"success": True, "message": "短信验证码已发送"}
    if settings.DEBUG:
        response_payload["debug_code"] = code
    return JsonResponse(response_payload)
