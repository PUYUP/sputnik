import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

from apps.person.utils.constants import CLIENT, CONSULTANT, REGISTERED


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta(AbstractUser.Meta):
        app_label = 'person'

    def roles_identifier(self):
        roles = self.roles.all().values_list('identifier', flat=True)
        return roles

    @property
    def is_registered(self):
        roles = self.roles_identifier()
        return REGISTERED in roles

    @property
    def is_client(self):
        roles = self.roles_identifier()
        return CLIENT in roles

    @property
    def is_consultant(self):
        roles = self.roles_identifier()
        return CONSULTANT in roles
