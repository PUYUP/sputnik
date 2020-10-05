from rest_framework import serializers

from utils.generals import get_model

Skill = get_model('master', 'Skill')


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        exclude = ('scope',)
