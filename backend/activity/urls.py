from django.urls import path

from . import views

urlpatterns = [
    path("logs", views.logs, name="logs"),
    path("stats", views.stats, name="stats"),
]
