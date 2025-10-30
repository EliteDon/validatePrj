from __future__ import annotations

import csv
from datetime import datetime
from typing import Iterable

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from activity.models import CaptchaType, LoginRecord

from .serializers import CaptchaTypeSerializer, LoginRecordSerializer


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CaptchaTypeListCreateView(generics.ListCreateAPIView):
    queryset = CaptchaType.objects.order_by("id")
    serializer_class = CaptchaTypeSerializer
    permission_classes = [permissions.IsAdminUser]


class CaptchaTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CaptchaType.objects.order_by("id")
    serializer_class = CaptchaTypeSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_destroy(self, instance: CaptchaType) -> None:
        was_default = instance.is_default
        super().perform_destroy(instance)
        if was_default and not CaptchaType.objects.filter(is_default=True).exists():
            fallback = CaptchaType.objects.filter(type_name="text").first()
            if fallback:
                fallback.is_default = True
                fallback.save(update_fields=["is_default"])


class LoginRecordListView(generics.ListAPIView):
    serializer_class = LoginRecordSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = AdminPagination

    def get_queryset(self):
        queryset = LoginRecord.objects.select_related("user").order_by("-login_time")
        params = self.request.query_params

        start_at = params.get("start")
        end_at = params.get("end")
        success = params.get("success")

        if start_at:
            start_dt = parse_datetime(start_at)
            if start_dt is None:
                try:
                    start_dt = datetime.fromisoformat(start_at)
                    if timezone.is_naive(start_dt):
                        start_dt = timezone.make_aware(start_dt)
                except ValueError:
                    start_dt = None
            if start_dt:
                queryset = queryset.filter(login_time__gte=start_dt)

        if end_at:
            end_dt = parse_datetime(end_at)
            if end_dt is None:
                try:
                    end_dt = datetime.fromisoformat(end_at)
                    if timezone.is_naive(end_dt):
                        end_dt = timezone.make_aware(end_dt)
                except ValueError:
                    end_dt = None
            if end_dt:
                queryset = queryset.filter(login_time__lte=end_dt)

        if success in {"true", "false", "1", "0"}:
            queryset = queryset.filter(success=success in {"true", "1"})

        return queryset

    def list(self, request, *args, **kwargs):
        if request.query_params.get("export") == "csv":
            queryset = self.filter_queryset(self.get_queryset())
            return self._export_csv(queryset)
        return super().list(request, *args, **kwargs)

    def _export_csv(self, queryset: Iterable[LoginRecord]) -> HttpResponse:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=login-records.csv"
        writer = csv.writer(response)
        writer.writerow(["用户名", "登录时间", "登录 IP", "设备信息", "状态"])
        for record in queryset:
            writer.writerow(
                [
                    record.username,
                    timezone.localtime(record.login_time).strftime("%Y-%m-%d %H:%M:%S"),
                    record.ip_address or "",
                    record.user_agent,
                    "成功" if record.success else "失败",
                ]
            )
        return response
