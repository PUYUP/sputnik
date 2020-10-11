from django.db.models import Q, Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from utils.generals import get_model
from apps.resume.utils.constants import DRAFT

Experience = get_model('resume', 'Experience')


class ExperienceListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        request = self.context.get('request')
        if value.exists():
            value = value.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))
        return super().to_representation(value)


class ExperienceSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        list_serializer_class = ExperienceListSerializer
        model = Experience
        fields = '__all__'

    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return data

    def to_representation(self, value):
        request = self.context.get('request')
        ret = super().to_representation(value)
        ret['is_creator'] = request.user.uuid == value.user.uuid
        ret['start_month_display'] = value.get_start_month_display()
        ret['employment_display'] = value.get_employment_display()

        if value.end_month:
            ret['end_month_display'] = value.get_end_month_display()
        return ret
