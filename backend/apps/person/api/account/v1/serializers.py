from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
# from firebase_admin.auth import get_user_by_phone_number

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
    def to_representation(self, value):
        if value.exists():
            value = value.prefetch_related(Prefetch('user')) \
                .select_related('user')
        return super().to_representation(value)


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
            # get data
            self.token = data.get('token', None)
            self.provider = data.get('provider', None)
            self.provider_value = data.get('provider_value', None)

            if settings.STRICT_MSISDN_DUPLICATE:
                self.fields['msisdn'].validators.extend([MSISDNDuplicateValidator()])

    def validate_msisdn(self, value):
        # check msisdn verified
        if settings.STRICT_MSISDN_VERIFIED:
            if self.instance:
                if self.provider == 'firebase':
                    """
                    Passcode provided by Firebase JavaScript SDK on the frontend
                    After passcode verified, we check the msisdn exists in Firebase with Python
                    """

                    """
                    formated_value = value.replace('0', '+62', 1);

                    try:
                       firebase_user = get_user_by_phone_number(formated_value)
                       firebase_msisdn = firebase_user._data.get('phoneNumber')
                       if firebase_msisdn != self.provider_value:
                           raise serializers.ValidationError(_(u"MSISDN tidak terdaftar"))
                    except:
                        raise serializers.ValidationError(_(u"Kode verifikasi pembaruan MSISDN salah"))
                    """
                    pass
                else:
                    with transaction.atomic():
                        try:
                            self.verifycode_obj = VerifyCode.objects.select_for_update() \
                                .get_verified_unused(msisdn=value, challenge=CHANGE_MSISDN, token=self.token)
                        except ObjectDoesNotExist:
                            raise serializers.ValidationError(_(u"Kode verifikasi pembaruan MSISDN salah"))
        return value

    def get_url(self, obj):
        request = self.context.get('request')
        url = reverse('person_api:user-detail', kwargs={'uuid': obj.user.uuid})

        return request.build_absolute_uri(url + 'account/')

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # remove custom field here, we don't need again
        data.pop('provider', None)
        data.pop('provider_value', None)

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

    def to_representation(self, value):
        data = super().to_representation(value)

        data['username'] = value.user.username
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    setattr(instance, key, value)
        instance.save()

        # all done mark verifycode used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return instance
