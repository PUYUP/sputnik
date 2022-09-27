from apps.helpdesk.models.models import SLA
from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField,
    WritetableFieldPutMethod
)

Priority = get_model('helpdesk', 'Priority')


class PriorityListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class PrioritySerializer(DynamicFieldsModelSerializer, WritetableFieldPutMethod,
                         serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:priority-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    sla = serializers.SlugRelatedField(slug_field='uuid', queryset=SLA.objects.all())

    class Meta:
        model = Priority
        list_serializer_class = PriorityListSerializer
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['identifier_display'] = value.get_identifier_display()
        return ret
