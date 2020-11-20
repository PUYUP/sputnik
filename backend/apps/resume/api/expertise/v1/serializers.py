from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)

Expertise = get_model('resume', 'Expertise')
Topic = get_model('master', 'Topic')


class ExpertiseListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    def to_representation(self, value):
        if isinstance(value, QuerySet):
            value = value.prefetch_related(Prefetch('topic')).select_related('topic')
        return super().to_representation(value)


class ExpertiseSerializer(DynamicFieldsModelSerializer, WritetableFieldPutMethod,
                          CleanValidateMixin, serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    topic = serializers.SlugRelatedField(slug_field='uuid', queryset=Topic.objects.all())

    class Meta:
        list_serializer_class = ExpertiseListSerializer
        model = Expertise
        fields = '__all__'

    def to_representation(self, value):
        request = self.context.get('request')
        ret = super().to_representation(value)

        ret['topic_label'] = value.topic.label
        ret['level_display'] = value.get_level_display()
        ret['is_creator'] = request.user.uuid == value.user.uuid

        return ret
