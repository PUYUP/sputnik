from rest_framework import permissions


class IsCurrentUserOrReject(permissions.BasePermission):
    def has_permission(self, request, view):
        # uuid from url param
        uuid = view.kwargs.get('uuid', 0)
        return uuid == str(request.user.uuid)


class IsEducationCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.user.uuid


class IsEducationAttachmentCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.education.user.uuid


class IsExperienceCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with experience creator
        return request.user.uuid == obj.user.uuid


class IsExperienceAttachmentCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with experience creator
        return request.user.uuid == obj.experience.user.uuid


class IsCertificateCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with certificate creator
        return request.user.uuid == obj.user.uuid


class IsCertificateAttachmentCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with certificate creator
        return request.user.uuid == obj.certificate.user.uuid


class IsExpertiseCreator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # current user_id compared with education creator
        return request.user.uuid == obj.user.uuid
