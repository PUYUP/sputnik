from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from utils.generals import get_model

Topic = get_model('helpdesk', 'Topic')


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        exclude = ('scope',)
