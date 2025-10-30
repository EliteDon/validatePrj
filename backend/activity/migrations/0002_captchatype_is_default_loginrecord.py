# Generated manually to add default captcha flag and login record model
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _set_default_captcha(apps, schema_editor):
    CaptchaType = apps.get_model("activity", "CaptchaType")
    if not CaptchaType.objects.filter(is_default=True).exists():
        text_captcha = CaptchaType.objects.filter(type_name="text").first()
        if text_captcha:
            text_captcha.is_default = True
            text_captcha.save(update_fields=["is_default"])


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="captchatype",
            name="is_default",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="captchatype",
            name="type_name",
            field=models.CharField(
                choices=[
                    ("text", "数字字母混合"),
                    ("puzzle", "拼图"),
                    ("image_select", "图片选图"),
                    ("email", "邮箱验证码"),
                    ("sms", "短信验证码"),
                    ("slider", "滑块"),
                    ("audio", "语音验证码"),
                ],
                max_length=50,
                unique=True,
            ),
        ),
        migrations.CreateModel(
            name="LoginRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("username", models.CharField(max_length=150)),
                (
                    "ip_address",
                    models.GenericIPAddressField(null=True, unpack_ipv4=True),
                ),
                ("user_agent", models.CharField(blank=True, max_length=200)),
                ("success", models.BooleanField(default=True)),
                ("login_time", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="login_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Login Record",
                "verbose_name_plural": "Login Records",
                "db_table": "captcha_api_loginrecord",
                "ordering": ["-login_time"],
            },
        ),
        migrations.RunPython(_set_default_captcha, _noop),
    ]
