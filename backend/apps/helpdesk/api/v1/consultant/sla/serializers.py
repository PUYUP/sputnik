from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer
from apps.helpdesk.api.v1.consultant.priority.serializers import PrioritySerializer

SLA = get_model('helpdesk', 'SLA')
Segment = get_model('helpdesk', 'Segment')


class SLAListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('priorities'))
        return super().to_representation(value)


class SLASerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:sla-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    priorities = PrioritySerializer(many=True, read_only=True)

    class Meta:
        model = SLA
        fields = '__all__'
        list_serializer_class = SLAListSerializer
