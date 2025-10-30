from django.urls import path

from . import views

urlpatterns = [
    path("register", views.register, name="register"),
    path("login", views.login_with_captcha, name="login"),
    path("send-email-code", views.send_email_code, name="send-email-code"),
    path("send-sms-code", views.send_sms_code, name="send-sms-code"),
]
