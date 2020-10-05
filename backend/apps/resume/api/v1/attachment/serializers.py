import os

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from utils.generals import get_model
from apps.resume.api.utils import handle_upload_attachment
from apps.resume.utils.validators import CleanValidateMixin

from rest_framework import serializers

Attachment = get_model('resume', 'Attachment')
Certificate = get_model('resume', 'Certificate')


class AttachmentSerializer(CleanValidateMixin, serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        attach_file = validated_data.pop('attach_file')
        obj = Attachment.objects.create(**validated_data)
        handle_upload_attachment(obj, attach_file)
        return obj
