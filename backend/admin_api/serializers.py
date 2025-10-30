from __future__ import annotations

from rest_framework import serializers

from activity.models import CaptchaType, LoginRecord


class CaptchaTypeSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_type_name_display", read_only=True)

    class Meta:
        model = CaptchaType
        fields = [
            "id",
            "type_name",
            "description",
            "config_json",
            "image_path",
            "is_default",
            "label",
        ]


class LoginRecordSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = LoginRecord
        fields = [
            "id",
            "username",
            "user",
            "ip_address",
            "user_agent",
            "success",
            "login_time",
        ]
