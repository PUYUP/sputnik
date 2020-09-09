import itertools

from django import forms
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    SetPasswordForm
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from utils.generals import get_model
from utils.validators import make_safe_string
from apps.person.utils.constants import ROLE_IDENTIFIERS, REGISTERED
from apps.person.utils.auth import set_roles, update_roles

User = get_model('person', 'User')
Role = get_model('person', 'Role')
RoleCapabilities = get_model('person', 'RoleCapabilities')

try:
    _ROLE_IDENTIFIERS = ROLE_IDENTIFIERS
except NameError:
    _ROLE_IDENTIFIERS = list()


try:
    _REGISTERED = REGISTERED
except NameError:
    _REGISTERED = list()


_USERNAME_VALIDATOR = UnicodeUsernameValidator()


class UserChangeFormExtend(UserChangeForm):
    """ Override user Edit form """
    email = forms.EmailField(max_length=254, help_text=_("Required. Inform a valid email address"))
    role = forms.MultipleChoiceField(
        choices=_ROLE_IDENTIFIERS,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text=_(u"Select roles for user")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial =  list(self.instance.roles.all().values_list('identifier', flat=True))

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email:
            # Validate each account has different email
            if User.objects.filter(email=email).exclude(username=username).exists():
                raise forms.ValidationError(_(u"Email {email} already registered.".format(email=email)))
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role', None)
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        
        roles = self.cleaned_data.get('role', None)
        if roles:
            update_roles(user=user, roles=roles)
        return user


class UserCreationFormExtend(UserCreationForm):
    """ Override user Add form """
    email = forms.EmailField(max_length=254, help_text=_("Required. Inform a valid email address"))
    role = forms.MultipleChoiceField(
        choices=_ROLE_IDENTIFIERS,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text=_(u"Select roles for user")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = _REGISTERED

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email:
            # Validate each account has different email
            if User.objects.filter(email=email).exclude(username=username).exists():
                raise forms.ValidationError(
                    _(u"Email {email} already registered.".format(email=email)),
                    passcode='email_used',
                )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

         # APPEND ROLES
        roles = self.cleaned_data.get('role', None)
        if roles:
            setattr(user, 'roles_value', roles)
        return user


# Register form
class RegisterForm(forms.Form):
    first_name = forms.CharField(label=_(u"Nama Lengkap"))
    username = forms.CharField(label=_(u"Nama Pengguna"), validators=[_USERNAME_VALIDATOR])
    email = forms.EmailField(label=_(u"Alamat Email"), widget=forms.EmailInput)
    password1 = forms.CharField(label=_(u"Kata Sandi"), strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    password2 = forms.CharField(label=_(u"Ulangi Kata Sandi"), strip=False,
                                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        email = self.request.session.get('otp_validate_email', None)

        # set default value
        kwargs.update(initial={'email': email})
        super().__init__(*args, **kwargs)

        if email:
            kwargs.update(initial={'email': email})
            self.fields['email'].widget.attrs['readonly'] = True

    def clean(self):
        super().clean()

        # clear unsafe html string
        cleaned_data = make_safe_string(self.cleaned_data)
        self.cleaned_data = cleaned_data

    def clean_username(self):
        email = self.request.session.get('email', False)
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exclude(email=email).exists():
            raise forms.ValidationError(_(u"Nama pengguna %s sudah terdaftar." % username))
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    _(u"The two password fields didn’t match"),
                    code='password_mismatch',
                )

        try:
            validate_password(password2)
        except ValidationError as e:
            raise forms.ValidationError(' '.join(e.messages))
        return password2


# Set new password
class SetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False
    )
