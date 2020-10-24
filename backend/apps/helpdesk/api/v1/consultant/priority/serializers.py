from apps.helpdesk.models.models import SLA
from rest_framework import serializers

from utils.generals import get_model
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer

Priority = get_model('helpdesk', 'Priority')


class PrioritySerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:priority-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    sla = serializers.SlugRelatedField(slug_field='uuid', queryset=SLA.objects.all())

    class Meta:
        model = Priority
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['identifier_display'] = value.get_identifier_display()
        return ret
