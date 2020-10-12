from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from rest_framework.exceptions import NotAcceptable
from apps.helpdesk.models.models import AttributeValue
from re import S
import re
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.utils import formats

from rest_framework import serializers
from utils.generals import get_model

Expertise = get_model('resume', 'Expertise')
Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')
Attribute = get_model('helpdesk', 'Attribute')


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


class AttributeSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = '__all__'


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
    attributes = AttributeSerializer(many=True, required=False, fields=('identifier',))

    class Meta:
        model = Schedule
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    def _get_content_type(self, instance):
        # Content type of Instance
        ct = ContentType.objects.get_for_model(instance, for_concrete_model=False)
        return ct

    def _attribute(self, instance, identifier):
        # Get Attribute object
        # :identifier egg: 'byweekday'
        ct = self._get_content_type(instance)
        try:
            attribute = Attribute.objects.get(content_type__id=ct.id, identifier=identifier)
        except ObjectDoesNotExist:
            return None
        return attribute

    def to_internal_value(self, data):
        attributes = data.get('attributes')
        attributes_identifier = list()
        attributes_value = list()

        if attributes:
            ct = ContentType.objects.get(app_label='helpdesk', model='schedule')
            for attr in attributes:
                attributes_identifier.append(attr.get('identifier'))
                attributes_value.append(attr.get('value'))

            attributes = Attribute.objects.filter(content_type__id=ct.id,
                                                  identifier__in=attributes_identifier)

        ret = super().to_internal_value(data)
        if attributes:
            ret['attributes'] = attributes
            ret['attributes_value'] = attributes_value
        return ret

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
        attributes = validated_data.pop('attributes')
        attributes_value = validated_data.pop('attributes_value')

        instance = Schedule.objects.create(**validated_data)
        for item in expertises:
            obj = ScheduleExpertise(schedule=instance, expertise=item['expertise'])
            schedule_expertises.append(obj)

        if schedule_expertises:
            try:
                ScheduleExpertise.objects.bulk_create(schedule_expertises, ignore_conflicts=False)
            except (Exception, IntegrityError) as e:
                raise NotAcceptable({'detail': repr(e)})

        # collect attributes
        if attributes and attributes_value:
            schedule_attributes = list()
            for index, item in enumerate(attributes):
                value = attributes_value[index]
                field = 'value_%s' % item.type
                field_value = {field: value}
                obj = AttributeValue(attribute=item, attribute_content_type=item.content_type,
                                     content_object=instance, **field_value)
                schedule_attributes.append(obj)

            if schedule_attributes:
                try:
                    AttributeValue.objects.bulk_create(schedule_attributes, ignore_conflicts=False)
                except (Exception, IntegrityError) as e:
                    raise NotAcceptable({'detail': repr(e)})

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

        ct = self._get_content_type(instance)
        print(ct)
        return instance
