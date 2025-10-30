from __future__ import annotations

import base64
import io
import math
import random
import string
import struct
import wave
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Tuple

from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import get_random_string

from activity.models import CaptchaType, SceneImage

try:  # pragma: no cover - optional dependency during tests
    from PIL import Image, ImageDraw, ImageFilter
except Exception:  # pragma: no cover
    Image = ImageDraw = ImageFilter = None  # type: ignore


CACHE_PREFIX = "captcha-token"


@dataclass
class CaptchaPayload:
    token: str
    type: str
    data: Dict[str, object]


class CaptchaService:
    """Utility helpers for generating captcha challenges."""

    @staticmethod
    def _store_expected_answer(token: str, *, answer: object, captcha_type: str) -> None:
        cache.set(
            f"{CACHE_PREFIX}:{token}",
            {"answer": answer, "captcha_type": captcha_type, "created_at": timezone.now()},
            timeout=60,
        )

    @staticmethod
    def generate_text_captcha(length: int = 5) -> CaptchaPayload:
        characters = string.ascii_uppercase + string.digits
        solution = "".join(random.choice(characters) for _ in range(length))
        token = get_random_string(32)
        image_data = CaptchaService._render_text(solution)
        CaptchaService._store_expected_answer(token, answer=solution, captcha_type="text")
        return CaptchaPayload(
            token=token,
            type="text",
            data={"image": image_data, "length": length},
        )

    @staticmethod
    def _render_text(text: str) -> str:
        if Image is None:
            return text  # Fallback for environments without Pillow
        width, height = 160, 60
        image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        for _ in range(5):
            start = (random.randint(0, width), random.randint(0, height))
            end = (random.randint(0, width), random.randint(0, height))
            color = tuple(random.randint(100, 200) for _ in range(3))
            draw.line([start, end], fill=color, width=2)

        try:
            from PIL import ImageFont

            font = ImageFont.load_default()
        except Exception:  # pragma: no cover
            font = None

        for index, char in enumerate(text):
            position = (10 + index * 28, random.randint(5, 15))
            color = tuple(random.randint(0, 150) for _ in range(3))
            draw.text(position, char, font=font, fill=color)

        image = image.filter(ImageFilter.SMOOTH)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def generate_slider_captcha() -> CaptchaPayload:
        token = get_random_string(32)
        background, piece, target_offset = CaptchaService._create_slider_assets()
        CaptchaService._store_expected_answer(token, answer=target_offset, captcha_type="slider")
        return CaptchaPayload(
            token=token,
            type="slider",
            data={"background": background, "piece": piece, "target_offset": target_offset},
        )

    @staticmethod
    def generate_puzzle_captcha() -> CaptchaPayload:
        token = get_random_string(32)
        background, piece, target_offset = CaptchaService._create_slider_assets()
        CaptchaService._store_expected_answer(token, answer=target_offset, captcha_type="puzzle")
        return CaptchaPayload(
            token=token,
            type="puzzle",
            data={"background": background, "piece": piece, "target_offset": target_offset},
        )

    @staticmethod
    def _create_slider_assets() -> Tuple[str, str, int]:
        if Image is None:
            placeholder = base64.b64encode(b"slider-placeholder").decode("utf-8")
            return (placeholder, placeholder, 30)
        width, height = 240, 120
        gap_width = 40
        gap_height = 40
        offset_x = random.randint(60, width - gap_width - 10)
        offset_y = random.randint(20, height - gap_height - 20)

        background = Image.new("RGB", (width, height), (240, 240, 240))
        draw = ImageDraw.Draw(background)
        for _ in range(80):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(10, 20)
            color = tuple(random.randint(120, 200) for _ in range(3))
            draw.ellipse((x, y, x + radius, y + radius), fill=color, outline=None)

        piece = Image.new("RGBA", (gap_width, gap_height))
        piece.paste(background.crop((offset_x, offset_y, offset_x + gap_width, offset_y + gap_height)))

        draw.rectangle((offset_x, offset_y, offset_x + gap_width, offset_y + gap_height), fill=(255, 255, 255))

        background_buffer = io.BytesIO()
        background.save(background_buffer, format="PNG")

        piece_buffer = io.BytesIO()
        piece.save(piece_buffer, format="PNG")

        background_encoded = base64.b64encode(background_buffer.getvalue()).decode("utf-8")
        piece_encoded = base64.b64encode(piece_buffer.getvalue()).decode("utf-8")
        return (f"data:image/png;base64,{background_encoded}", f"data:image/png;base64,{piece_encoded}", offset_x)

    @staticmethod
    def generate_image_selection() -> CaptchaPayload:
        token = get_random_string(32)
        categories = list(SceneImage.objects.values_list("category", flat=True).distinct())
        if categories:
            category = random.choice(categories)
            candidates = list(SceneImage.objects.filter(category=category).order_by("id")[:9])
        else:
            category = "cat"
            candidates = []
        selected_ids: List[int] = []
        for image in candidates:
            selected_ids.append(image.id)

        CaptchaService._store_expected_answer(token, answer=sorted(selected_ids), captcha_type="image_select")
        return CaptchaPayload(
            token=token,
            type="image_select",
            data={
                "category": category,
                "images": [
                    {"id": image.id, "file_path": image.file_path, "category": image.category}
                    for image in candidates
                ],
            },
        )

    @staticmethod
    def generate_audio_captcha(length: int = 4) -> CaptchaPayload:
        code = "".join(random.choice(string.digits) for _ in range(length))
        token = get_random_string(32)
        audio_data = CaptchaService._synthesize_tone_sequence(code)
        CaptchaService._store_expected_answer(token, answer=code, captcha_type="audio")
        return CaptchaPayload(
            token=token,
            type="audio",
            data={"audio": audio_data, "length": length},
        )

    @staticmethod
    def _synthesize_tone_sequence(code: str) -> str:
        frame_rate = 16000
        amplitude = 16000
        duration_per_digit = 0.35
        silence_duration = 0.12

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(frame_rate)

            for digit in code:
                frequency = 400 + int(digit) * 35
                for index in range(int(frame_rate * duration_per_digit)):
                    value = int(
                        amplitude
                        * math.sin(2 * math.pi * frequency * (index / frame_rate))
                    )
                    wav_file.writeframes(struct.pack("<h", value))
                for _ in range(int(frame_rate * silence_duration)):
                    wav_file.writeframes(struct.pack("<h", 0))

        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:audio/wav;base64,{encoded}"


class CaptchaVerifier:
    @staticmethod
    def verify(token: str, answer: object) -> Tuple[bool, str, str]:
        cache_key = f"{CACHE_PREFIX}:{token}"
        payload = cache.get(cache_key)
        if not payload:
            return False, "expired", "验证码已过期或不存在"

        expected = payload["answer"]
        captcha_type = payload["captcha_type"]

        if captcha_type == "text":
            if isinstance(answer, str) and answer.upper() == str(expected).upper():
                cache.delete(cache_key)
                return True, captcha_type, "验证成功"
        elif captcha_type in {"slider", "puzzle"}:
            try:
                offset = int(answer)
            except (TypeError, ValueError):
                return False, captcha_type, "滑块位置无效"
            tolerance = 5
            if abs(offset - int(expected)) <= tolerance:
                cache.delete(cache_key)
                return True, captcha_type, "验证成功"
        elif captcha_type == "image_select":
            if isinstance(answer, list) and sorted(int(x) for x in answer) == list(expected):
                cache.delete(cache_key)
                return True, captcha_type, "验证成功"
        elif captcha_type == "audio":
            if isinstance(answer, str) and answer.strip() == str(expected):
                cache.delete(cache_key)
                return True, captcha_type, "验证成功"

        return False, captcha_type, "验证码错误"


def get_default_captcha_type() -> CaptchaType:
    captcha_type = CaptchaType.objects.filter(is_default=True).first()
    if captcha_type:
        return captcha_type

    captcha_type, _ = CaptchaType.objects.get_or_create(
        type_name="text",
        defaults={
            "description": "默认字符验证码",
            "config_json": {"length": 5},
            "is_default": True,
        },
    )
    return captcha_type


class VerificationCodeService:
    EMAIL_CACHE_PREFIX = "email-code"
    SMS_CACHE_PREFIX = "sms-code"

    @staticmethod
    def _cache_key(prefix: str, target: str) -> str:
        return f"{prefix}:{target}"

    @staticmethod
    def _generate_numeric_code(length: int = 6) -> str:
        return "".join(random.choice(string.digits) for _ in range(length))

    @classmethod
    def create_email_code(cls, email: str, length: int = 6) -> str:
        code = cls._generate_numeric_code(length)
        cache.set(
            cls._cache_key(cls.EMAIL_CACHE_PREFIX, email),
            {"code": code, "expires_at": timezone.now() + timedelta(minutes=5)},
            timeout=300,
        )
        return code

    @classmethod
    def validate_email_code(cls, email: str, code: str) -> bool:
        cache_key = cls._cache_key(cls.EMAIL_CACHE_PREFIX, email)
        payload = cache.get(cache_key)
        if payload and payload.get("code") == str(code).strip():
            cache.delete(cache_key)
            return True
        return False

    @classmethod
    def create_sms_code(cls, phone: str, length: int = 6) -> str:
        code = cls._generate_numeric_code(length)
        cache.set(
            cls._cache_key(cls.SMS_CACHE_PREFIX, phone),
            {"code": code, "expires_at": timezone.now() + timedelta(minutes=5)},
            timeout=300,
        )
        return code

    @classmethod
    def validate_sms_code(cls, phone: str, code: str) -> bool:
        cache_key = cls._cache_key(cls.SMS_CACHE_PREFIX, phone)
        payload = cache.get(cache_key)
        if payload and payload.get("code") == str(code).strip():
            cache.delete(cache_key)
            return True
        return False
