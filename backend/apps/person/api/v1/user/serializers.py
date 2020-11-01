
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db.models.query import QuerySet
from django.http import request
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import EmailValidator

from rest_framework import serializers

# PROJECT UTILS
from utils.generals import get_model
from utils.validators import non_python_keyword, identifier_validator

from apps.person.api.validator import (
    EmailDuplicateValidator,
    MSISDNDuplicateValidator,
    MSISDNNumberValidator,
    PasswordValidator
)
from ..account.serializers import AccountSerializer
from ..profile.serializers import ProfileSerializer

# Resume
from apps.resume.api.v1.education.serializers import EducationSerializer
from apps.resume.api.v1.certificate.serializers import CertificateSerializer
from apps.resume.api.v1.experience.serializers import ExperienceSerializer
from apps.resume.api.v1.expertise.serializers import ExpertiseSerializer

User = get_model('person', 'User')
Account = get_model('person', 'Account')
VerifyCode = get_model('person', 'VerifyCode')
Role = get_model('person', 'Role')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('identifier',)

    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean(from_restful=True)
        return attrs


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields_used = kwargs.pop('fields_used', None)
        context = kwargs.get('context', dict())
        request = context.get('request', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        # Use this field on specific request
        if request.method == 'PATCH':
            # Only this field can us at user update
            fields_used = ('username', 'password', 'first_name', 'email',)

        if fields_used is not None and fields_used != '__all__':
            # Drop any fields that are not specified in the `fields_used` argument.
            allowed = set(fields_used)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserListSerializer(serializers.ListSerializer):
    def to_representation(self, value):
        print(value)
        if isinstance(value, QuerySet):
            print('AAAAAAAAAAAA')
            value = value.prefetch_related(Prefetch('topic'))
        return super().to_representation(value)


class UserSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='person_api:user-detail',
                                               lookup_field='uuid', read_only=True)

    profile = ProfileSerializer(many=False, read_only=True)
    account = AccountSerializer(many=False, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    certificate = CertificateSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    expertise = ExpertiseSerializer(many=True, read_only=True)

    # for registration only
    # msisdn not part of User model
    # msisdn part of Account
    msisdn = serializers.CharField(required=False, write_only=True,
                                   validators=[MSISDNNumberValidator()],
                                   min_length=8, max_length=14)

    # for registration only
    # set user role at register
    role = RoleSerializer(many=True)

    # use if action need verify code
    # eg: register, change email, ect
    token = serializers.CharField(required=False, write_only=True)
    challenge = serializers.CharField(required=False, write_only=True,
                                      validators=[non_python_keyword,
                                                  identifier_validator])

    # change password purposed
    password1 = serializers.CharField(required=False, write_only=True)
    password2 = serializers.CharField(required=False, write_only=True)

    # for display purpose only
    role_identifier = serializers.SlugRelatedField(slug_field='identifier', many=True,
                                                   read_only=True, source='role')
    permalink = serializers.SerializerMethodField(read_only=True)
    expertise_label = serializers.SlugRelatedField(slug_field='topic_label', read_only=True, many=True,
                                                   source='expertise')

    class Meta:
        model = User
        list_serializer_class = UserListSerializer
        exclude = ('id', 'user_permissions', 'groups', 'date_joined',
                   'is_superuser', 'last_login', 'is_staff',)
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6
            },
            'username': {
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'required': False,
                'validators': [EmailValidator()]
            }
        }

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        # default verifycode
        self.verifycode_obj = None

        # data
        data = kwargs.get('data', dict())

        self.msisdn = data.get('msisdn', None)
        self.challenge = data.get('challenge', None)
        self.token = data.get('token', None)

        self.email = data.get('email', None)
        self.role = data.get('role', None)

        # used for password change only
        self.password = data.get('password', None) # as old password
        self.password1 = data.get('password1', None)
        self.password2 = data.get('password2', None)

        # remove password validator if update
        if self.instance and self.password1 and self.password2:
            pass
        else:
            if 'password' in self.fields:
                self.fields['password'].validators.extend([PasswordValidator()])

        if settings.STRICT_MSISDN and 'msisdn' in self.fields:
            # MSISDN required if EMAIL not provided
            if not self.email:
                self.fields['msisdn'].required = True

            if settings.STRICT_MSISDN_DUPLICATE:
                self.fields['msisdn'].validators.extend([MSISDNDuplicateValidator()])

        if settings.STRICT_EMAIL and 'email' in self.fields:
            # EMAIL required if MSISDN not provided
            if not self.msisdn:
                self.fields['email'].required = True

            if settings.STRICT_EMAIL_DUPLICATE:
                self.fields['email'].validators.extend([EmailDuplicateValidator()])

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # remove custom field here, we don't need again
        data.pop('challenge', None)
        data.pop('token', None)
        data.pop('password1', None)
        data.pop('password2', None)

        # set is_active to True
        # if False user can't loggedin
        data['is_active'] = True
        return data

    def validate_role(self, value):
        # make user only allow one role
        if len(value) > 1:
            raise serializers.ValidationError(_(u"Multiple role not allowed"))
        return value

    def validate_email(self, value):
        # check verified email
        if settings.STRICT_EMAIL_VERIFIED:
            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(email=value, challenge=self.challenge, token=self.token)
                except ObjectDoesNotExist:
                    if self.instance:
                        # update user
                        raise serializers.ValidationError(_(u"Kode verifikasi pembaruan email salah"))
                    else:
                        # create user
                        raise serializers.ValidationError(_(u"Alamat email belum divalidasi"))
        return value

    def validate_msisdn(self, value):
        # check msisdn verified
        if settings.STRICT_MSISDN_VERIFIED:
            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(msisdn=value, challenge=self.challenge, token=self.token)
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(_(u"MSISDN belum divalidasi"))
        return value

    """
    def validate_username(self, value):
        if self.instance:
            email = self.instance.email
            msisdn = self.instance.account.msisdn

            with transaction.atomic():
                try:
                    self.verifycode_obj = VerifyCode.objects.select_for_update() \
                        .get_verified_unused(email=email, msisdn=msisdn, challenge=self.challenge,
                                             token=self.token)
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(_(u"Kode verifikasi pembaruan nama pengguna salah"))
        return value
    """

    def validate_password(self, value):
        instance = getattr(self, 'instance', dict())
        if instance:
            username = getattr(instance, 'username', None)

            # make sure new and old password filled
            if not self.password1 or not self.password2:
                raise serializers.ValidationError(_(u"Kata sandi lama dan baru wajib"))
            
            print(self.password2)
            if self.password1 != self.password2:
                raise serializers.ValidationError(_(u"Kata sandi lama dan baru tidak sama"))

            try:
                validate_password(self.password2)
            except ValidationError as e:
                raise serializers.ValidationError(e.messages)

            # check current password is passed
            passed = authenticate(username=username, password=self.password)
            if passed is None:
                raise serializers.ValidationError(_(u"Kata sandi lama salah"))
            return self.password2
        return value

    @transaction.atomic
    def create(self, validated_data):
        self.role = validated_data.pop('role')

        try:
            user = User.objects.create_user(**validated_data)
        except IntegrityError as e:
            raise ValidationError(str(e))
        except TypeError as e:
            raise ValidationError(str(e))

        # create Account instance
        if self.msisdn:
            account = getattr(user, 'account')
            if account:
                account.msisdn = self.msisdn
                account.save()
            else:
                try:
                    Account.objects.create(user=user, msisdn=self.msisdn)
                except IntegrityError:
                    pass

        # set role
        if self.role:
            role_list = list()
            for r in self.role:
                i = Role(user=user, **r)
                role_list.append(i)

            if role_list:
                Role.objects.bulk_create(role_list, ignore_conflicts=False)

        # all done mark verifycode as used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request', None)

        for key, value in validated_data.items():
            if hasattr(instance, key):
                # update password
                if key == 'password':
                    instance.set_password(value)

                    # add flash message
                    messages.success(request, _("Kata sandi berhasil dirubah."
                                                " Login dengan kata sandi baru Anda"))
                else:
                    old_value = getattr(instance, key, None)
                    if old_value != value:
                        setattr(instance, key, value)
        instance.save()

        # all done mark verifycode as used
        if self.verifycode_obj:
            self.verifycode_obj.mark_used()
        return instance
