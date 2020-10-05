from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from utils.generals import get_model
from apps.person.utils.constants import CHANGE_MSISDN
from apps.person.api.validator import (
    MSISDNDuplicateValidator,
    MSISDNNumberValidator
)

Account = get_model('person', 'Account')
Profile = get_model('person', 'Profile')
VerifyCode = get_model('person', 'VerifyCode')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('picture', 'headline',)


class AccountListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        request = self.context.get('request')
        if data.exists():
            data = data.prefetch_related(Prefetch('user')) \
                .select_related('user')
        return super().to_representation(data)


# User account serializer
class AccountSerializer(serializers.ModelSerializer):
    # used for validate only if update eg: update msisdn
    token = serializers.CharField(read_only=True, required=False)
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        list_serializer_class = AccountListSerializer
        model = Account
        exclude = ('user', 'id', 'create_date', 'update_date',)
        extra_kwargs = {
            'msisdn': {
                'min_length': 8,
                'max_length': 14,
                'validators': [MSISDNNumberValidator()]
            }
        }
    
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # default verifycode
        self.token = None
        self.verifycode_obj = None

        # data available only on PATCH and POST
        data = kwargs.get('data', None)
        if data:
            # get token
            self.token = data.get('token', None)

            if settings.STRICT_MSISDN_DUPLICATE:
                self.fields['msisdn'].validators.extend([MSISDNDuplicateValidator()])

    def validate_msisdn(self, value):
        # check msisdn verified
        if settings.STRICT_MSISDN_VERIFIED:
            if self.instance:
                with transaction.atomic():
                    try:
                        self.verifycode_obj = VerifyCode.objects.select_for_update() \
                            .get_verified_unused(msisdn=value, challenge=CHANGE_MSISDN, token=self.token)
                    except ObjectDoesNotExist:
                        raise serializers.ValidationError(_(u"Kode verifikasi pembaruan msisdn salah"))
        return value

    def get_url(self, obj):
        request = self.context.get('request')
        url = reverse('person_api:user-detail', kwargs={'uuid': obj.user.uuid})

        return request.build_absolute_uri(url + 'account/')

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # one field each update request
        if len(data) > 1:
            raise serializers.ValidationError({
                'field': _("Hanya boleh satu data")
            })

        # field can't empty to
        if len(data) == 0:
            raise serializers.ValidationError({
                'field': _("Tidak ada yang diperbarui")
            })
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['username'] = instance.user.username
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if value and old_value != value:
                    setattr(instance, key, value)
        instance.save()

        # all done mark verifycode used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return instance
