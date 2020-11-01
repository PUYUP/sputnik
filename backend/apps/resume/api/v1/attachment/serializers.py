from django.db import transaction
from django.utils.translation import gettext_lazy as _

from utils.generals import get_model
from utils.files import handle_upload_attachment
from apps.resume.utils.validators import CleanValidateMixin

from rest_framework import serializers

Attachment = get_model('resume', 'Attachment')


class AttachmentSerializer(CleanValidateMixin, serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        file = validated_data.pop('file')
        instance, _created = Attachment.objects.get_or_create(**validated_data)
        handle_upload_attachment(instance, file)
        return instance
