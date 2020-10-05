from django.db.models import Q, Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from utils.generals import get_model
from apps.resume.utils.constants import DRAFT

Experience = get_model('resume', 'Experience')


class ExperienceListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        request = self.context.get('request')
        if data.exists():
            data = data.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))
        return super().to_representation(data)


class ExperienceSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        list_serializer_class = ExperienceListSerializer
        model = Experience
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)
        ret['is_creator'] = request.user.uuid == instance.user.uuid
        ret['start_month_display'] = instance.get_start_month_display()
        ret['employment_display'] = instance.get_employment_display()

        if instance.end_month:
            ret['end_month_display'] = instance.get_end_month_display()
        return ret
