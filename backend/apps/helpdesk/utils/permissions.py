from rest_framework import permissions


class IsConsultantOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_consultant
