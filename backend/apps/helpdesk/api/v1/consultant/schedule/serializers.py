from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import formats

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.helpdesk.models.models import Recurrence
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer
from apps.helpdesk.api.v1.consultant.segment.serializers import SegmentSerializer

from ..rrule.serializers import RuleSerializer

Expertise = get_model('resume', 'Expertise')
Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')


class ScheduleExpertiseSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    expertise = serializers.SlugRelatedField(slug_field='uuid', queryset=Expertise.objects.all())

    class Meta:
        model = ScheduleExpertise
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['expertise_label'] = value.expertise_label
        return ret


""" RECURRENCES """
class RecurrenceSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    schedule = serializers.SlugRelatedField(slug_field='uuid', queryset=Schedule.objects.all())
    rules = RuleSerializer(many=True, read_only=True, fields=('uuid', 'identifier', 'mode', 'type',
                                                              'url', 'rule_values',))

    class Meta:
        model = Recurrence
        fields = '__all__'

    def get_url(self, obj):
        from .views import ScheduleApiView

        schedule_uuid = obj.schedule.uuid
        recurrence_uuid = obj.uuid
        view = ScheduleApiView()
        view.basename = 'helpdesk_api:consultant:schedule'
        view.request = self.context.get('request')
        url = view.reverse_action('recurrences-update', args=[schedule_uuid, recurrence_uuid])
        return url
    
    def to_representation(self, value):
        ret = super().to_representation(value)
 
        ret['dtstart_formated'] = formats.date_format(value.dtstart, 'DATETIME_FORMAT')
        if value.dtuntil:
            ret['dtuntil_formated'] = formats.date_format(value.dtuntil, 'DATETIME_FORMAT')

        return ret

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        try:
            instance = Recurrence.objects.create(**validated_data)
        except (ValidationError, Exception) as e:
            raise NotAcceptable({'detail': repr(e)})
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if value and old_value != value:
                    setattr(instance, key, value)

        instance.save()
        return instance


class ScheduleListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        schedule_uuid = self.context.get('uuid', None)
        if value.exists() and schedule_uuid:
            value = value.prefetch_related(Prefetch('segments'), Prefetch('expertises'))
        return super().to_representation(value)


class ScheduleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:schedule-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule_expertises = ScheduleExpertiseSerializer(many=True, fields=('uuid', 'expertise', 'expertise_label',))

    # display purpose
    recurrence = RecurrenceSerializer(many=False, read_only=True)
    expertises = serializers.SlugRelatedField(slug_field='expertise_label', read_only=True,
                                              many=True, source='schedule_expertises')
    segments = SegmentSerializer(many=True, read_only=True,
                                 fields=('uuid', 'slas', 'canal', 'canal_display', 'url',
                                         'open_hour', 'close_hour', 'max_opened', 'is_active',))
 
    class Meta:
        model = Schedule
        fields = '__all__'
        list_serializer_class = ScheduleListSerializer

    def to_representation(self, value):
        request = self.context.get('request')
        ret = super().to_representation(value)

        ret['permalink'] = request.build_absolute_uri(value.permalink)
        return ret

    @transaction.atomic
    def create(self, validated_data):
        schedule_expertises = list()
        expertises = validated_data.pop('schedule_expertises')
        instance = Schedule.objects.create(**validated_data)

        # set expertises
        for item in expertises:
            print(item)
            obj = ScheduleExpertise(schedule=instance, expertise=item['expertise'])
            schedule_expertises.append(obj)

        if schedule_expertises:
            try:
                ScheduleExpertise.objects.bulk_create(schedule_expertises, ignore_conflicts=False)
            except (Exception, IntegrityError) as e:
                raise NotAcceptable({'detail': repr(e)})
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        expertises_uuid = list()
        submited_expertises = list()
        expertises = validated_data.pop('schedule_expertises', None)

        if expertises:
            # extract Expertise only, not ScheduleExpertise
            # this submited by user in frontend
            for item in expertises:
                expertise = item.get('expertise', '')
                if expertise:
                    submited_expertises.append(expertise)
                    expertises_uuid.append(expertise.uuid)

            # current user expertises
            x = list()
            current_expertises = instance.schedule_expertises.filter(Q(expertise__uuid__in=expertises_uuid))
            for item in current_expertises:
                x.append(item.expertise)

            # collect removed ScheduleExpertise
            removed_expertises = instance.schedule_expertises.exclude(Q(expertise__uuid__in=expertises_uuid))
            if removed_expertises.exists():
                removed_expertises.delete()

            # collect new expertises, fresh not exists in database
            create_expertises = list()
            new_expertises = list(set(submited_expertises) - set(x))
            if new_expertises:
                for item in new_expertises:
                    obj = ScheduleExpertise(schedule=instance, expertise=item)
                    create_expertises.append(obj)

            # bulk created
            if create_expertises:
                ScheduleExpertise.objects.bulk_create(create_expertises)

        # update instance
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if value and old_value != value:
                    setattr(instance, key, value)

        instance.save()
        return instance
