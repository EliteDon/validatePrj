from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/captcha/", include("captcha_api.urls")),
    path("api/activity/", include("activity.urls")),
]
