import os

from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable
from apps.person.utils.constants import DRAFT

from utils.generals import get_model
from apps.person.utils.auth import CurrentUserDefault
from apps.person.api.utils import handle_upload_attachment

Certificate = get_model('person', 'Certificate')
CertificateAttachment = get_model('person', 'CertificateAttachment')


class CertificateListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        request = self.context.get('request')
        if data.exists():
            data = data.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))
        return super().to_representation(data)


class CertificateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        list_serializer_class = CertificateListSerializer
        model = Certificate
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['is_creator'] = request.user.uuid == instance.user.uuid
        ret['attachment_count'] = instance.certificate_attachments.count()
        return ret

    @transaction.atomic
    def create(self, validated_data):
        obj = Certificate.objects.create(**validated_data)
        return obj


class CertificateAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateAttachment
        exclude = ('certificate',)

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['is_creator'] = request.user.uuid == instance.certificate.user.uuid
        return ret

    @transaction.atomic
    def create(self, validated_data):
        parent_instance = self.context['parent_instance']
        attach_file = validated_data.pop('attach_file')
        obj = CertificateAttachment.objects.create(certificate_id=parent_instance.id, **validated_data)
        handle_upload_attachment(obj, parent_instance._meta.model_name, attach_file)
        return obj
