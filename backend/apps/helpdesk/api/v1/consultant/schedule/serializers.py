from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import formats

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)
from apps.helpdesk.models.models import ScheduleTerm
from apps.helpdesk.api.v1.consultant.segment.serializers import SegmentSerializer
from apps.helpdesk.api.v1.consultant.rule.serializers import RuleSerializer

Expertise = get_model('resume', 'Expertise')
Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')


""" EXPERTISES """
class ScheduleExpertiseListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class ScheduleExpertiseSerializer(DynamicFieldsModelSerializer, WritetableFieldPutMethod,
                                  serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:expertise-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule = serializers.SlugRelatedField(slug_field='uuid', queryset=Schedule.objects.all())
    expertise = serializers.SlugRelatedField(slug_field='uuid', queryset=Expertise.objects.all())

    class Meta:
        model = ScheduleExpertise
        list_serializer_class = ScheduleExpertiseListSerializer
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['expertise_label'] = value.expertise_label
        return ret


""" TERMS """
class ScheduleTermSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:scheduleterm-detail',
                                               lookup_field='uuid', read_only=True)
    schedule = serializers.SlugRelatedField(slug_field='uuid', write_only=True, queryset=Schedule.objects.all())
    rule = RuleSerializer(many=True, read_only=True, fields_used=('uuid', 'identifier', 'mode', 'type',
                                                                  'url', 'rule_value', 'direction',))

    class Meta:
        model = ScheduleTerm
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)

        ret['freq_identifier'] = value.get_freq_display()
        ret['dtstart_formated'] = formats.date_format(value.dtstart, 'DATETIME_FORMAT')
        if value.dtuntil:
            ret['dtuntil_formated'] = formats.date_format(value.dtuntil, 'DATETIME_FORMAT')

        return ret

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = ScheduleTerm.objects.get_or_create(**validated_data)
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


""" SCHEDULE """
class ScheduleListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        if isinstance(value, QuerySet):
            value = value.prefetch_related(Prefetch('segment'))

        return super().to_representation(value)


class ScheduleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:schedule-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule_expertise = ScheduleExpertiseSerializer(many=True, read_only=True,
                                                     fields_used=('uuid', 'expertise', 'expertise_label',))

    # display purpose
    schedule_term = ScheduleTermSerializer(many=False, read_only=True)
    expertise = serializers.SlugRelatedField(slug_field='expertise_label', read_only=True,
                                             many=True, source='schedule_expertise')
    segment = SegmentSerializer(many=True, read_only=True,
                                fields_used=('uuid', 'sla', 'canal', 'canal_display', 'url', 'quota',
                                             'open_hour', 'close_hour', 'max_opened', 'is_active',))

    # for display purpose only
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Schedule
        list_serializer_class = ScheduleListSerializer
        fields = '__all__'
        
    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink)

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Schedule.objects.get_or_create(**validated_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # update instance
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    setattr(instance, key, value)

        instance.save()
        return instance
