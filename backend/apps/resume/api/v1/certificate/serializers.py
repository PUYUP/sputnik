from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from utils.generals import get_model
from apps.resume.utils.constants import DRAFT

Certificate = get_model('resume', 'Certificate')


class CertificateListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        request = self.context.get('request')
        if value.exists():
            value = value.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .exclude(~Q(user__uuid=request.user.uuid) & Q(status=DRAFT))
        return super().to_representation(value)


class CertificateSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='resume:certificate-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        list_serializer_class = CertificateListSerializer
        model = Certificate
        fields = '__all__'

    def to_representation(self, value):
        request = self.context.get('request')
        ret = super().to_representation(value)

        ret['is_creator'] = request.user.uuid == value.user.uuid
        ret['issued_formated'] = formats.date_format(value.issued, 'DATE_FORMAT')
        if value.expired:
            ret['expired_formated'] = formats.date_format(value.expired, 'DATE_FORMAT')

        return ret

    @transaction.atomic
    def create(self, validated_data):
        obj = Certificate.objects.create(**validated_data)
        return obj
