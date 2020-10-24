from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer
from apps.helpdesk.api.v1.consultant.sla.serializers import SLASerializer

Segment = get_model('helpdesk', 'Segment')
Schedule = get_model('helpdesk', 'Schedule')

class SegmentListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('slas'))
        return super().to_representation(value)


class SegmentSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:segment-detail',
                                               lookup_field='uuid', read_only=True)
    schedule = serializers.SlugRelatedField(slug_field='uuid', queryset=Schedule.objects.all())
    slas = SLASerializer(many=True, read_only=True)

    class Meta:
        model = Segment
        fields = '__all__'
        list_serializer_class= SegmentListSerializer

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['canal_display'] = value.get_canal_display()
        ret['open_hour_formated'] = value.open_hour.strftime("%I:%M")
        ret['close_hour_formated'] = value.close_hour.strftime("%I:%M")

        return ret
