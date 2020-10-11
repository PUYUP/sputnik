from re import S
from django.db import transaction
from django.db.models import Q
from django.forms.utils import pretty_name
from django.utils import formats

from rest_framework import serializers
from utils.generals import get_model

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

        ret['expertise_label'] = value.expertise.topic.label
        return ret


class ScheduleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:schedule-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule_expertises = ScheduleExpertiseSerializer(many=True, fields=('uuid', 'expertise',))

    class Meta:
        model = Schedule
        fields = '__all__'

    def to_representation(self, value):
        ret = super().to_representation(value)

        ret['dtstart_formated'] = formats.date_format(value.dtstart, 'DATE_FORMAT')
        if value.dtuntil:
            ret['dtuntil_formated'] = formats.date_format(value.dtuntil, 'DATE_FORMAT')

        return ret

    @transaction.atomic
    def create(self, validated_data):
        schedule_expertises = list()
        expertises = validated_data.pop('schedule_expertises')

        instance = Schedule.objects.create(**validated_data)
        for item in expertises:
            obj = ScheduleExpertise(schedule=instance, expertise=item['expertise'])
            schedule_expertises.append(obj)

        if schedule_expertises:
            ScheduleExpertise.objects.bulk_create(schedule_expertises, ignore_conflicts=False)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        expertises_uuid = list()
        submited_expertises = list()
        expertises = validated_data.pop('schedule_expertises')
        
        # extract Expertise only, not ScheduleExpertise
        # this submited by user in frontend
        for item in expertises:
            expertise = item['expertise']
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
