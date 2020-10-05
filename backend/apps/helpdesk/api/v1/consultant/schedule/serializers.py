from django.db import transaction
from django.db.models import Prefetch

from rest_framework import serializers
from utils.generals import get_model

Schedule = get_model('helpdesk', 'Schedule')


class ScheduleSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

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
