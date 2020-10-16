from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction
from django.db.models import Q
from django.utils import formats

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.helpdesk.models.models import Recurrence, Rule, RuleValue

Expertise = get_model('resume', 'Expertise')
Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
 
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None and fields != '__all__':
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ScheduleExpertiseSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    expertise = serializers.SlugRelatedField(slug_field='uuid', queryset=Expertise.objects.all())

    class Meta:
        model = ScheduleExpertise
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['expertise_label'] = value.expertise_label
        return ret


class RuleValueSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = RuleValue
        fields = '__all__'


class RuleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    rule_values = RuleValueSerializer(many=True, fields=('value_integer', 'value_varchar', 'value_datetime',))

    class Meta:
        model = Rule
        fields = '__all__'


""" RECURRENCES """
class RecurrenceSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    # set to None because 'default' is required
    # we set schedule object in to_internal_value
    schedule = serializers.HiddenField(default=None)

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
        schedule = self.context.get('schedule')
        data = super().to_internal_value(data)

        data['schedule'] = schedule
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


class ScheduleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:schedule-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule_expertises = ScheduleExpertiseSerializer(many=True, fields=('uuid', 'expertise', 'expertise_label',))

    # display purpose
    recurrence = RecurrenceSerializer(many=False, read_only=True)
    expertises = serializers.SlugRelatedField(slug_field='expertise_label', read_only=True,
                                              many=True, source='schedule_expertises')
 
    class Meta:
        model = Schedule
        fields = '__all__'

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
