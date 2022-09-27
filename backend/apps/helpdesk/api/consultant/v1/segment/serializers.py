from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import DynamicFieldsModelSerializer
from ..sla.serializers import SLASerializer

Segment = get_model('helpdesk', 'Segment')
Schedule = get_model('helpdesk', 'Schedule')

class SegmentListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('sla'))
        return super().to_representation(value)


class SegmentSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:segment-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule = serializers.SlugRelatedField(slug_field='uuid', queryset=Schedule.objects.all())
    sla = SLASerializer(many=True, read_only=True)

    # property from model, read-only
    canal_label = serializers.CharField(read_only=True)
    open_hour_formated = serializers.TimeField(read_only=True)
    close_hour_formated = serializers.TimeField(read_only=True)

    class Meta:
        model = Segment
        fields = '__all__'
        # list_serializer_class= SegmentListSerializer
