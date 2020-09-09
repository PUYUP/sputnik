import os

from django.db import transaction
from django.db.models import Q, Prefetch
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable
from apps.person.utils.constants import DRAFT

from utils.generals import get_model
from apps.person.utils.auth import CurrentUserDefault

Certificate = get_model('person', 'Certificate')
CertificateAttachment = get_model('person', 'CertificateAttachment')


def handle_upload_attachment(instance, file):
    if instance and file:
        name, ext = os.path.splitext(file.name)

        fsize = file.size / 1000
        if fsize > 5000:
            raise serializers.ValidationError({'detail': _("Ukuran file maksimal 5 MB")})
    
        if ext != '.jpeg' and ext != '.jpg' and ext != '.png' and ext != '.pdf':
            raise serializers.ValidationError({'detail': _("Jenis file tidak diperbolehkan")})

        certificate = getattr(instance, 'certificate')
        username = certificate.user.username
        title = certificate.title
        filename = '{username}_{title}'.format(username=username, title=title)
        filename_slug = slugify(filename)

        instance.attach_type = ext
        instance.attach_file.save('%s%s' % (filename_slug, ext), file, save=False)
        instance.save(update_fields=['attach_file', 'attach_type'])


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
        certificate = self.context['certificate']
        attach_file = validated_data.pop('attach_file')
        obj = CertificateAttachment.objects.create(certificate_id=certificate.id, **validated_data)
        handle_upload_attachment(obj, attach_file)
        return obj
