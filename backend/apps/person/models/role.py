import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission

from utils.validators import IDENTIFIER_VALIDATOR, non_python_keyword
from apps.person.utils.constants import ROLES_ALLOWED, ROLE_IDENTIFIERS, REGISTERED

try:
    _REGISTERED = REGISTERED
except NameError:
    _REGISTERED = None

try:
    _ROLE_IDENTIFIERS = ROLE_IDENTIFIERS
except NameError:
    _ROLE_IDENTIFIERS = list()


class AbstractRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='roles')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)
    identifier = models.CharField(choices=_ROLE_IDENTIFIERS, default=_REGISTERED, max_length=255,
                                  validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    # we need to restrict this role active or not
    # example roles: [client] and [consultant]
    # role as [client] must active (in other way this action take by admin)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _(u"Role")
        verbose_name_plural = _(u"Roles")

    def __str__(self):
        return self.identifier

    def clean(self, *args, **kwargs):
        from_restful = kwargs.get('from_restful')
        if (self.identifier not in dict(ROLE_IDENTIFIERS)) or (from_restful and self.identifier not in dict(ROLES_ALLOWED)):
            raise ValidationError(
                {'identifier': _(u"Role %s not available." % (self.identifier))}
            )


class AbstractRoleCapabilities(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    identifier = models.CharField(choices=ROLE_IDENTIFIERS, max_length=255,
                                  validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    permissions = models.ManyToManyField(Permission, related_name='role_capabilities',
                                         related_query_name='role_capability')

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _(u"Role Capability")
        verbose_name_plural = _(u"Role Capabilities")
        constraints = [
            models.UniqueConstraint(fields=['identifier'], name='unique_identifier_capability')
        ]

    def __str__(self):
        return self.identifier
