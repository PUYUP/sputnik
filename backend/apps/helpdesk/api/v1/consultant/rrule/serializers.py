from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.helpdesk.api.fields import DynamicFieldsModelSerializer

Rule = get_model('helpdesk', 'Rule')
RuleValue = get_model('helpdesk', 'RuleValue')
Recurrence = get_model('helpdesk', 'Recurrence')


class RuleValueSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = RuleValue
        exclude = ('rule',)


class RuleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:rule-detail',
                                               lookup_field='uuid', read_only=True)
    recurrence = serializers.SlugRelatedField(slug_field='uuid', queryset=Recurrence.objects.all())
    rule_values = RuleValueSerializer(many=True, fields=('uuid', 'value_varchar', 'value_integer', 'value_datetime',))

    class Meta:
        model = Rule
        fields = '__all__'
        extra_kwargs = {
            'type': {'required': True},
            'recurrence': {'write_only': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        rule_values = validated_data.pop('rule_values', None)
        recurrence = validated_data.get('recurrence')
        instance, _created = Rule.objects.get_or_create(**validated_data)

        if rule_values:
            value_type = 'value_%s' % instance.type
            bulk_create_values = list()

            for item in rule_values:
                value = item.get(value_type, None)
                if value:
                    value_set = {value_type: value}
                    obj = RuleValue(rule=instance, recurrence=recurrence, **value_set)
                    bulk_create_values.append(obj)

            if bulk_create_values:
                try:
                    RuleValue.objects.bulk_create(bulk_create_values, ignore_conflicts=False)
                except (IntegrityError, Exception) as e:
                    raise NotAcceptable({'detail': repr(e)})

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        rule_values = validated_data.pop('rule_values', None)
        if rule_values:
            bulk_update_values = list()
            value_type = 'value_%s' % instance.type
            value_uuids = [item.get('uuid') if item.get('uuid', None) else '' for item in rule_values]

            current_rule_values = instance.rule_values.filter(uuid__in=value_uuids)
            if current_rule_values:
                for current in current_rule_values:
                    for item in rule_values:
                        if str(item.get('uuid')) == str(current.uuid):
                            setattr(current, value_type, item.get(value_type, ''))
                            bulk_update_values.append(current)

            if bulk_update_values:
                try:
                    RuleValue.objects.bulk_update(bulk_update_values, fields=[value_type])
                except (IntegrityError, Exception) as e:
                    raise NotAcceptable({'detail': repr(e)})

        instance.refresh_from_db()
        return instance
