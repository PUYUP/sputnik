from django.utils.translation import ugettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model

Expertise = get_model('resume', 'Expertise')
Skill = get_model('master', 'Skill')


class ExpertiseListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        if data.exists():
            data = data.prefetch_related(Prefetch('skill')).select_related('skill')
        return super().to_representation(data)


class ExpertiseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    skill = serializers.SlugRelatedField(slug_field='uuid', queryset=Skill.objects.all())

    class Meta:
        # list_serializer_class = ExpertiseListSerializer
        model = Expertise
        fields = '__all__'

    def to_representationX(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['skill_label'] = instance.skill.label
        ret['is_creator'] = request.user.uuid == instance.user.uuid
        return ret
