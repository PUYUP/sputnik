from django.db.models import Q, Prefetch
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)
from apps.resume.utils.constants import DRAFT

Education = get_model('resume', 'Education')


class EducationListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    def to_representation(self, value):
        request = self.context.get('request')
        
        if isinstance(value, QuerySet):
            value = value.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))

        return super().to_representation(value)


class EducationSerializer(DynamicFieldsModelSerializer, CleanValidateMixin, WritetableFieldPutMethod,
                          serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='resume:education-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        list_serializer_class = EducationListSerializer
        model = Education
        fields = '__all__'

    def to_representation(self, value):
        request = self.context.get('request')
        ret = super().to_representation(value)
        ret['is_creator'] = request.user.uuid == value.user.uuid

        return ret
