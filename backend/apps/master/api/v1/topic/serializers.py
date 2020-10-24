from django.db import transaction
from rest_framework import serializers

from utils.generals import get_model

Topic = get_model('master', 'Topic')
Scope = get_model('master', 'Scope')


class ScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    scopes = serializers.SlugRelatedField(many=True, read_only=True,
                                          slug_field='label')

    class Meta:
        model = Topic
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')

        # restrict used this params
        if not request.user.is_staff:
            _is_active = validated_data.pop('is_active', None)
            _is_approved = validated_data.pop('is_approved', None)

        defaults = {'label': validated_data.get('label')}
        instance, _created = Topic.objects.get_or_create(**validated_data, defaults=defaults)
        return instance
