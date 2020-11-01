from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)

Rule = get_model('helpdesk', 'Rule')
RuleValue = get_model('helpdesk', 'RuleValue')
ScheduleTerm = get_model('helpdesk', 'ScheduleTerm')


class RuleValueListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


class RuleValueSerializer(DynamicFieldsModelSerializer, WritetableFieldPutMethod,
                          serializers.ModelSerializer):
    rule = serializers.SlugRelatedField(slug_field='uuid', queryset=Rule.objects.all())

    class Meta:
        model = RuleValue
        list_serializer_class = RuleValueListSerializer
        fields = '__all__'

    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs
    
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['uuid'] = value.uuid
        return ret


class RuleSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:rule-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    schedule_term = serializers.SlugRelatedField(slug_field='uuid', queryset=ScheduleTerm.objects.all())
    rule_value = RuleValueSerializer(many=True, read_only=True,
                                     fields_used=('uuid', 'value_varchar', 'value_integer', 'value_datetime',))

    class Meta:
        model = Rule
        fields = '__all__'
        extra_kwargs = {
            'type': {'required': True},
            'schedule_term': {'write_only': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = Rule.objects.get_or_create(**validated_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    setattr(instance, key, value)

        instance.save()
        instance.refresh_from_db()
        return instance
