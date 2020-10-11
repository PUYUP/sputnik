from rest_framework import serializers

from utils.generals import get_model

Topic = get_model('master', 'Topic')
Scope = get_model('master', 'Scope')


class ScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scope
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    scopes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='label'
     )

    class Meta:
        model = Topic
        fields = '__all__'
