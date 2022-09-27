import uuid

from django.db import models
from django.db.models import Count
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _

from apps.person.utils.constants import CLIENT, CONSULTANT, REGISTERED


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta(AbstractUser.Meta):
        app_label = 'person'

    def role_identifier(self):
        role = self.role.all().values_list('identifier', flat=True)
        return role

    @property
    def is_registered(self):
        role = self.role_identifier()
        return REGISTERED in role

    @property
    def is_client(self):
        role = self.role_identifier()
        return CLIENT in role

    @property
    def is_consultant(self):
        role = self.role_identifier()
        return CONSULTANT in role

    @property
    def is_resume_complete(self):
        resume_count = self.__class__.objects.filter(id=self.id) \
            .aggregate(education=Count('education', distinct=True),
                       experience=Count('experience', distinct=True),
                       expertise=Count('expertise', distinct=True))

        education_count = resume_count.get('education', 0)
        experience_count = resume_count.get('experience', 0)
        expertise_count = resume_count.get('expertise', 0)

        if education_count > 0 and experience_count > 0 and expertise_count > 0:
            return True
        return False

    @property
    def permalink(self):
        from django.urls import reverse
        return reverse('person_view:user_detail', kwargs={'uuid': self.uuid})
