import itertools

from django.db.models import Prefetch
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import _unicode_ci_compare
from django.contrib.auth.validators import UnicodeUsernameValidator

from utils.generals import get_model
from apps.person.utils.constants import VerifyCode_SESSION_FIELDS

validate_username = UnicodeUsernameValidator()

User = get_model('person', 'User')


class CurrentUserDefault:
    """Return current logged-in user"""
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        self.user = user

    def __call__(self):
        return self.user

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class LoginBackend(ModelBackend):
    """Login w/h username or email"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            # user = User._default_manager.get_by_natural_key(username)
            # You can customise what the given username is checked against, here I compare to both username and email fields of the User model
            user = User.objects \
                .filter(
                    Q(username__iexact=username)
                    | Q(email__iexact=username)
                    | Q(account__msisdn=username)
                    & Q(account__msisdn_verified=True))
        except User.DoesNotExist:
            # Run the default password tokener once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            try:
                user = user.get(Q(username__iexact=username) | Q(email__iexact=username)
                                | Q(account__msisdn=username)
                                & Q(account__msisdn_verified=True))
            except User.DoesNotExist:
                return None

            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        return super().authenticate(request, username, password, **kwargs)


class GuestRequiredMixin:
    """Verify that the current user guest."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('home'))
        return super().dispatch(request, *args, **kwargs)


def get_users_by_email(email):
    """Given an email, return matching user(s) who should receive a reset.
    This allows subclasses to more easily customize the default policies
    that prevent inactive users and users with unusable passwords from
    resetting their password.
    """
    email_field_name = User.get_email_field_name()
    active_users = User._default_manager.filter(**{
        '%s__iexact' % email_field_name: email,
        'is_active': True,
    })
    return (
        u for u in active_users
        if u.has_usable_password() and
        _unicode_ci_compare(email, getattr(u, email_field_name))
    )


def clear_verifycode_session(request, interact):
    # clear verifycode session
    for key in VerifyCode_SESSION_FIELDS:
        try:
            del request.session['verifycode_%s_%s' % (interact, key)]
        except KeyError:
            pass


def set_role(user=None, role=list()):
    """
    :user is user object
    :role is list of identifier for role, egg: ['registered', 'client']
    """
    RoleCapability = get_model('person', 'RoleCapability')

    role_created = list()
    identifier_initial = list(user.role.values_list('identifier', flat=True))
    identifier_new = list(set(role) - set(identifier_initial))

    for identifier in identifier_new:
        role_obj = user.role.model(user=user, identifier=identifier)
        role_created.append(role_obj)

    if role_created:
        user.role.model.objects.bulk_create(role_created)

    capability_objs = RoleCapability.objects \
        .prefetch_related(Prefetch('permission')) \
        .filter(identifier__in=user.role.all().values('identifier'))
    permission_objs = [list(item.permission.all()) for item in capability_objs]
    permission_objs_unique = list(set(itertools.chain.from_iterable(permission_objs)))
    user.user_permissions.add(*permission_objs_unique)


def update_role(user=None, role=list()):
    """
    :user is user object
    :role is list of identifier for role, egg: ['registered', 'client']
    """
    RoleCapability = get_model('person', 'RoleCapability')

    permission_removed = list()
    permission_add = list()
    permission_current = user.user_permissions.all()
    capability = RoleCapability.objects \
        .prefetch_related(Prefetch('permission'))

    # REMOVE ROLE
    role_removed = user.role.exclude(identifier__in=role)
    if role_removed.exists():
        capability = capability.filter(identifier__in=role_removed.values('identifier'))
        permission = [list(item.permission.all()) for item in capability]
        permission_removed = list(set(itertools.chain.from_iterable(permission)))
        role_removed.delete()

    # ADD ROLE
    if role:
        role_created = list()
        identifier_initial = list(user.role.values_list('identifier', flat=True))
        identifier_new = list(set(role) ^ set(identifier_initial))

        for identifier in identifier_new:
            role_obj = user.role.model(user=user, identifier=identifier)
            role_created.append(role_obj)

        if role_created:
            user.role.model.objects.bulk_create(role_created)

        capability = capability.filter(identifier__in=user.role.all().values('identifier'))
        permission = [list(item.permission.all()) for item in capability]
        permission_add = list(set(itertools.chain.from_iterable(permission)))

    # Compare current with new permission
    # If has different assign that to user
    if permission_current:
        add_diff = list(set(permission_add) & set(permission_current))
        if add_diff:
            add_diff = list(set(permission_add) ^ set(add_diff))
    else:
        add_diff = list(set(permission_add))

    if add_diff and permission_add:
        user.user_permissions.add(*list(add_diff))

    # Compare current with old permission
    # If has different remove that
    removed_diff = list(set(permission_add) ^ set(permission_removed))
    if removed_diff and permission_removed:
        diff = set(removed_diff) & set(permission_removed)
        user.user_permissions.remove(*list(diff))
