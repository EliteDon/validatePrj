from django.urls import path

from . import views

urlpatterns = [
    path("available", views.available, name="captcha_available"),
    path("request", views.request_captcha, name="captcha_request"),
    path("verify", views.verify, name="captcha_verify"),
    path("types", views.upsert_type, name="captcha_upsert"),
    path("types/<int:type_id>", views.delete_type, name="captcha_delete"),
]
