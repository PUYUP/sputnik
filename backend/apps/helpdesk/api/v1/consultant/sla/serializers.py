from django.db import transaction
from django.db.models import Prefetch
from django.db.models import query
from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer
from apps.helpdesk.api.v1.consultant.priority.serializers import PrioritySerializer

SLA = get_model('helpdesk', 'SLA')
Segment = get_model('helpdesk', 'Segment')
Priority = get_model('helpdesk', 'Priority')


class SLAListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('priorities'))
        return super().to_representation(value)


class SLASerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:sla-detail',
                                               lookup_field='uuid', read_only=True)
    segment = serializers.SlugRelatedField(slug_field='uuid', queryset=Segment.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    priorities = PrioritySerializer(many=True, required=True,
                                    fields=('cost', 'label', 'user', 'identifier', 'uuid',))

    class Meta:
        model = SLA
        fields = '__all__'
        list_serializer_class = SLAListSerializer

    def to_internal_value(self, data):
        priorities = data.get('priorities', None)
        priorities_uuid = [item.get('uuid', None) for item in priorities]

        ret = super().to_internal_value(data)
        ret['priorities_uuid'] = priorities_uuid
        return ret

    @transaction.atomic
    def create(self, validated_data):
        priorities = validated_data.pop('priorities', None)
        _priorities_uuid = validated_data.pop('priorities_uuid', None)
        
        instance = SLA.objects.create(**validated_data)

        # bulk create priority
        if priorities:
            priorities_created = list()
            for p in priorities:
                o = Priority(sla=instance, **p)
                priorities_created.append(o)
            
            if priorities_created:
                try:
                    Priority.objects.bulk_create(priorities_created, ignore_conflicts=False)
                except (IntegrityError, Exception) as e:
                    raise NotAcceptable(detail=repr(e))

        instance.refresh_from_db()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        priorities = validated_data.pop('priorities', None)
        priorities_uuid = validated_data.pop('priorities_uuid', None)

        # create priority if not exits
        priorities_uuid_none_indexs = [i for i,v in enumerate(priorities_uuid) if v == None]
        priorities_created = list()

        if priorities_uuid_none_indexs:
            for i in priorities_uuid_none_indexs:
                p = priorities[i]
                o = Priority(sla=instance, user=instance.user, **p)
                priorities_created.append(o)

            if priorities_created:
                try:
                    Priority.objects.bulk_create(priorities_created, ignore_conflicts=False)
                except (IntegrityError, Exception) as e:
                    raise NotAcceptable(detail=repr(e))

        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if value and old_value != value:
                    setattr(instance, key, value)

        # bulk update priority
        if priorities_uuid:
            priority_objs = instance.priorities.filter(uuid__in=priorities_uuid)
            if priority_objs.exists():
                priorities_updated = list()

                for item in priority_objs:
                    index = priorities_uuid.index(str(item.uuid))
                    p = priorities[index]
                    cost = p.get('cost', None)
                    label = p.get('label', None)

                    if cost:
                        setattr(item, 'cost', cost)
                    if label:
                        setattr(item, 'label', label)
                
                    priorities_updated.append(item)

                # bulk update
                if priorities_updated:
                    try:
                        Priority.objects.bulk_update(priorities_updated, fields=['cost', 'label'])
                    except (IntegrityError, Exception) as e:
                        raise NotAcceptable(detail=repr(e))

        instance.save()
        instance.refresh_from_db()
        return instance
