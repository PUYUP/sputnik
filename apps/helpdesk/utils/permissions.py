from rest_framework import permissions


class IsExpertiseCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.user.uuid
