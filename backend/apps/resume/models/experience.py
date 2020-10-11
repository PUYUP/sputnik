import uuid
from dateutil.rrule import MO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from utils.constants import MONTH_CHOICES_STR
from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.resume.utils.validators import year_validator, month_validator
from apps.resume.utils.constants import (
    EMPLOYMENT_CHOICES,
    EXPERIENCE_STATUS,
    DRAFT
)


class AbstractExperience(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='experiences')
    attachments = GenericRelation('resume.Attachment', content_type_field='content_type',
                                  object_id_field='object_id', related_query_name='experience')

    title = models.CharField(max_length=255)
    employment = models.CharField(choices=EMPLOYMENT_CHOICES, max_length=255,
                                  validators=[non_python_keyword, IDENTIFIER_VALIDATOR])
    company = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    currently = models.BooleanField(default=True, verbose_name=_(u"Currently working here?"))
    start_month = models.CharField(choices=MONTH_CHOICES_STR, max_length=2,
                                   validators=[month_validator])
    start_year = models.CharField(max_length=4, validators=[year_validator])
    end_month = models.CharField(choices=MONTH_CHOICES_STR, null=True, blank=True, max_length=2,
                                 validators=[month_validator])
    end_year = models.CharField(null=True, blank=True, max_length=4, validators=[year_validator])
    description = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(default=1, null=True)
    status = models.CharField(choices=EXPERIENCE_STATUS, max_length=15,
                              default=DRAFT, null=True)

    class Meta:
        abstract = True
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _(u"Experience")
        verbose_name_plural = _(u"Experiences")

    def __str__(self):
        return self.user.username

    def clean(self, *args, **kwargs):
        if not self.currently:
            if not self.end_month:
                raise ValidationError({'end_month': _(u"End month required")})

            if not self.end_year:
                raise ValidationError({'end_year': _(u"End year required")})

    def save(self, *args, **kwargs):
        if self.user and not self.pk:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            self.sort_order = c + 1
        super().save(*args, **kwargs)
