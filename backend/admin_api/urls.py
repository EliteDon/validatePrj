from django.urls import path

from .views import CaptchaTypeDetailView, CaptchaTypeListCreateView, LoginRecordListView

urlpatterns = [
    path("captcha-types/", CaptchaTypeListCreateView.as_view(), name="admin-captcha-type-list"),
    path(
        "captcha-types/<int:pk>/",
        CaptchaTypeDetailView.as_view(),
        name="admin-captcha-type-detail",
    ),
    path("login-records/", LoginRecordListView.as_view(), name="admin-login-records"),
]
