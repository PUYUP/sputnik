from rest_framework import serializers

from utils.generals import get_model
from apps.person.api.account.serializers import ProfileSerializer

User = get_model('person', 'User')


class ExpertSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(many=False, read_only=True)

    class Meta:
        model = User
        fields = ('uuid', 'username', 'first_name', 'profile',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return ret
