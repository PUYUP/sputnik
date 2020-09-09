from django.db import transaction
from django.db.models import Prefetch

from rest_framework import serializers

from utils.generals import get_model
from apps.person.utils.auth import CurrentUserDefault

Schedule = get_model('helpdesk', 'Schedule')
Expertise = get_model('helpdesk', 'Expertise')


class ExpertiseSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Expertise
        fields = '__all__'


class ScheduleSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Schedule
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        method = request.method

        if method == 'GET':
            # show the expertise as json object
            self.fields['expertise'] = serializers.StringRelatedField(many=True)
