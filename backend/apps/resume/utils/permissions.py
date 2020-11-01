from rest_framework import permissions


class IsObjectOwnerOrReject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.user.uuid
