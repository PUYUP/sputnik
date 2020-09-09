from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from apps.person.utils.auth import CurrentUserDefault

Expertise = get_model('helpdesk', 'Expertise')
Topic = get_model('helpdesk', 'Topic')


class ExpertiseListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        if data.exists():
            data = data.prefetch_related(Prefetch('topic')).select_related('topic')
        return super().to_representation(data)


class ExpertiseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        list_serializer_class = ExpertiseListSerializer
        model = Expertise
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['topic_subject'] = instance.topic.subject
        ret['is_creator'] = request.user.uuid == instance.user.uuid
        return ret
