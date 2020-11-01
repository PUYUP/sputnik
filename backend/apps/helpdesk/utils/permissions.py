from django.utils.translation import gettext_lazy as _
from rest_framework import permissions


class IsConsultantOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_consultant


class IsResumeCompleteOrReject(permissions.BasePermission):
    message = _("Resume belum lengkap. Harap lengkapi.")

    def has_permission(self, request, view):
        return request.user.is_resume_complete


class IsObjectOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid


class IsRuleValueOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.rule.user.uuid


class IsScheduleTermOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.schedule.user.uuid
