import os

from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.person.utils.auth import CurrentUserDefault
from apps.person.utils.constants import DRAFT
from apps.person.api.utils import handle_upload_attachment

Experience = get_model('person', 'Experience')
ExperienceAttachment = get_model('person', 'ExperienceAttachment')


class ExperienceListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        request = self.context.get('request')
        if data.exists():
            data = data.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))
        return super().to_representation(data)


class ExperienceSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        list_serializer_class = ExperienceListSerializer
        model = Experience
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['is_creator'] = request.user.uuid == instance.user.uuid
        ret['attachment_count'] = instance.experience_attachments.count()
        ret['start_month_display'] = instance.get_start_month_display()
        ret['employment_display'] = instance.get_employment_display()

        if instance.end_month:
            ret['end_month_display'] = instance.get_end_month_display()
        return ret


class ExperienceAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceAttachment
        exclude = ('experience',)

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['is_creator'] = request.user.uuid == instance.experience.user.uuid
        return ret

    @transaction.atomic
    def create(self, validated_data):
        parent_instance = self.context['parent_instance']
        attach_file = validated_data.pop('attach_file')
        obj = ExperienceAttachment.objects.create(experience_id=parent_instance.id, **validated_data)
        handle_upload_attachment(obj, parent_instance._meta.model_name, attach_file)
        return obj
