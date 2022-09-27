from django.db import transaction
from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import DynamicFieldsModelSerializer
from ..priority.serializers import PrioritySerializer

SLA = get_model('helpdesk', 'SLA')
Segment = get_model('helpdesk', 'Segment')
Priority = get_model('helpdesk', 'Priority')


class SLAListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('priority'))
        return super().to_representation(value)


class SLASerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:sla-detail',
                                               lookup_field='uuid', read_only=True)
    segment = serializers.SlugRelatedField(slug_field='uuid', queryset=Segment.objects.all(),
                                           write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    priority = PrioritySerializer(many=True, read_only=True,
                                  fields_used=('cost', 'label', 'user', 'identifier', 'uuid',))

    # for display purpose. read-only
    label_verbose = serializers.CharField(read_only=True)

    class Meta:
        model = SLA
        fields = '__all__'
        # list_serializer_class = SLAListSerializer

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = SLA.objects.get_or_create(**validated_data)
        instance.refresh_from_db()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    setattr(instance, key, value)

        instance.save()
        return instance
