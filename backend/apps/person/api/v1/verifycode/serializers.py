from pprint import pp
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.core.validators import EmailValidator
from django.template import context
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model

User = get_model('person', 'User')
VerifyCode = get_model('person', 'VerifyCode')


class VerifyCodeFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        data = kwargs.get('data', None)
        context = kwargs.get('context', None)
        request = context.get('request', None)

        if data:
            email = data.get('email', None)
            msisdn = data.get('msisdn', None)
            account = data.get('account', None)

            if request.method == 'POST' and (not email or not msisdn or not account):
                if account:
                    self.fields.pop('msisdn')
                    self.fields.pop('email')
                else:
                    if email:
                        self.fields.pop('msisdn')
                    elif msisdn:
                        self.fields.pop('email')

                    try:
                        self.fields.pop('account')
                    except KeyError:
                        pass


class VerifyCodeSerializer(VerifyCodeFieldsModelSerializer, serializers.ModelSerializer):
    account = serializers.CharField(read_only=True)

    class Meta:
        model = VerifyCode
        fields = ('uuid', 'account', 'email', 'msisdn', 'challenge', 'token', 'valid_until',)
        read_only_fields = ('uuid', 'token',)
        extra_kwargs = {
            'challenge': {
                'required': True
            },
            'msisdn': {
                'required': True,
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': True
            },
        }

    def get_msisdn(self, obj):
        if obj.msisdn:
            return obj.msisdn
        else:
            request = self.context.get('request', None)
            user = request.user
            return user.account.msisdn

    def to_representation(self, value):
        info = _("Terjadi kesalahan")
        if value.email:
            info = _("Kode verifikasi dikirim ke email <strong>{email}</strong>".format(email=value.email))

        if value.msisdn:
            info = _("Kode verifikasi dikirim ke nomor <strong>{msisdn}</strong>".format(msisdn=value.msisdn))

        # capture data from context params
        request = self.context.get('request', None)
        is_validate = self.context.get('is_validate', False)
        user = request.user

        # normalize
        ret = super().to_representation(instance)

        if hasattr(instance, 'msisdn'):
            ret['msisdn'] = instance.msisdn
        else:
            if user:
                account = getattr(user, 'account', dict())
                ret['msisdn'] = getattr(account, 'msisdn', None)

        if hasattr(instance, 'email'):
            ret['email'] = instance.email
        else:
            if user:
                ret['email'] = user.email

        # this data not for validate response
        if not is_validate:
            ret['created'] = getattr(instance, 'created', None)
            ret['info'] = info

        # prepare for password recovery
        password_recovery_token = self.context.get('password_recovery_token', None)
        password_recovery_uidb64 = self.context.get('password_recovery_uidb64', None)
        if password_recovery_token and password_recovery_uidb64:
            ret['password_recovery_token'] = password_recovery_token
            ret['password_recovery_uidb64'] = password_recovery_uidb64

        return ret

    def to_internal_value(self, data):
        account = None
        email = data.get('email')
        msisdn = data.get('msisdn')
        account = data.get('account')

        # normalize
        data = super().to_internal_value(data)

        # fill email by account found
        # TODO: use msisdn
        if account and not email and not msisdn:
            try:
                user = User.objects.get(Q(username=account) | Q(email=account) | Q(account__msisdn=account))
                data['email'] = getattr(user, 'email', None)
            except ObjectDoesNotExist:
                pass
        return data

    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request', None)
        email = validated_data.pop('email', None)
        msisdn = validated_data.pop('msisdn', None)
        challenge = validated_data.pop('challenge', None)
        user_agent = request.META['HTTP_USER_AGENT']

        if not email and not msisdn:
            raise NotAcceptable(_(u"Email, msisdn or account required (one of these)"))

        _defaults = {
            'challenge': challenge,
            'user_agent': user_agent,
            'is_verified': False,
            'is_used': False,
            'is_expired': False,
        }

        if email and not msisdn:
            _defaults['email'] = email

        if msisdn and not email:
            _defaults['msisdn'] = msisdn

        # Ops, please choose one (email or telehone)
        if msisdn and email:
            raise NotAcceptable(_(u"Only accept one of email or msisdn"))

        # If `valid_until` greater than time now we update VerifyCode Code
        obj, created = VerifyCode.objects \
            .filter(Q(valid_until__gt=timezone.now())) \
            .update_or_create(**_defaults, defaults=_defaults) 

        setattr(obj, 'created', created)
        return obj

    @transaction.atomic
    def update(self, instance):
        setattr(instance, 'created', False)
        context = self.request.get('context')
        is_validate_action = context.get('is_validate_action')

        # update verifycode
        if is_validate_action:
            # this mean validate verifycode send in email or msisdn
            instance.save(update_fields=['is_verified'])
        else:
            # this mean request new verifycode
            instance.save(update_fields=['passcode', 'token', 'valid_until',
                                        'valid_until_timestamp'])
        return instance
