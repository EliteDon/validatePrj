from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from activity.models import CaptchaType
from activity.services import log_captcha_event

from .services import CaptchaService, CaptchaVerifier, get_default_captcha_type


def _parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_GET
def available(request):
    data = list(
        CaptchaType.objects.values(
            "id", "type_name", "description", "config_json", "image_path", "is_default"
        )
    )
    if not data:
        captcha_type = get_default_captcha_type()
        data = [
            {
                "id": captcha_type.id,
                "type_name": captcha_type.type_name,
                "description": captcha_type.description,
                "config_json": captcha_type.config_json,
                "image_path": captcha_type.image_path,
                "is_default": captcha_type.is_default,
            }
        ]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
@require_http_methods(["POST"])
def request_captcha(request):
    payload = _parse_json(request)
    captcha_type = payload.get("type", "text")

    if captcha_type == "text":
        config = payload.get("config", {})
        length = int(config.get("length", 5))
        challenge = CaptchaService.generate_text_captcha(length=length)
    elif captcha_type == "slider":
        challenge = CaptchaService.generate_slider_captcha()
    elif captcha_type == "puzzle":
        challenge = CaptchaService.generate_puzzle_captcha()
    elif captcha_type == "image_select":
        challenge = CaptchaService.generate_image_selection()
    elif captcha_type == "audio":
        config = payload.get("config", {})
        length = int(config.get("length", 4))
        challenge = CaptchaService.generate_audio_captcha(length=length)
    else:
        challenge = CaptchaService.generate_text_captcha()

    return JsonResponse(
        {
            "success": True,
            "data": challenge.data,
            "token": challenge.token,
            "type": challenge.type,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def verify(request):
    payload = _parse_json(request)
    token = payload.get("token")
    answer = payload.get("answer")

    if not token:
        return JsonResponse({"success": False, "message": "缺少 token"}, status=400)

    success, captcha_type, message = CaptchaVerifier.verify(token, answer)
    log_captcha_event(
        request=request,
        captcha_type=captcha_type,
        result="success" if success else "failed",
        message=message,
        user_id=request.user.id if request.user.is_authenticated else None,
    )
    return JsonResponse({"success": success, "type": captcha_type, "message": message})


@csrf_exempt
@require_http_methods(["POST"])
@user_passes_test(lambda user: user.is_staff)
@login_required
def upsert_type(request):
    payload = _parse_json(request)
    type_id = payload.get("id")
    defaults = {
        "type_name": payload.get("type_name", ""),
        "description": payload.get("description", ""),
        "config_json": payload.get("config_json", {}),
        "image_path": payload.get("image_path", ""),
        "is_default": payload.get("is_default", False),
    }
    if not defaults["type_name"]:
        return JsonResponse({"success": False, "message": "type_name 必填"}, status=400)

    if type_id:
        CaptchaType.objects.filter(id=type_id).update(**defaults)
        captcha_type = CaptchaType.objects.get(id=type_id)
    else:
        captcha_type = CaptchaType.objects.create(**defaults)

    return JsonResponse({"success": True, "data": {
        "id": captcha_type.id,
        "type_name": captcha_type.type_name,
        "description": captcha_type.description,
        "config_json": captcha_type.config_json,
        "image_path": captcha_type.image_path,
        "is_default": captcha_type.is_default,
    }})


@csrf_exempt
@require_http_methods(["DELETE"])
@user_passes_test(lambda user: user.is_staff)
@login_required
def delete_type(request, type_id: int):
    deleted, _ = CaptchaType.objects.filter(id=type_id).delete()
    return JsonResponse({"success": bool(deleted)})
