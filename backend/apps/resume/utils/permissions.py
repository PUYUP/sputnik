from rest_framework import permissions


class IsAttachmentCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.uuid == obj.content_object.user.uuid


class IsEducationCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.user.uuid


class IsExperienceCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with experience creator
        return request.user.uuid == obj.user.uuid


class IsCertificateCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with certificate creator
        return request.user.uuid == obj.user.uuid


class IsExpertiseCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.user.uuid
