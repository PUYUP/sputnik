import uuid
import os

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.person.utils.constants import (
    EMPLOYMENT_CHOICES,
    EDUCATION_STATUS,
    DRAFT
)


class AbstractEducation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='educations')

    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, null=True, blank=True)
    study = models.CharField(max_length=255, null=True, blank=True)
    start_year = models.CharField(max_length=4, null=True, blank=True)
    end_year = models.CharField(max_length=4, null=True, blank=True)
    grade = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    sort_order = models.IntegerField(default=1, null=True)
    status = models.CharField(choices=EDUCATION_STATUS, max_length=15,
                              default=DRAFT, null=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-create_date']
        verbose_name = _(u"Education")
        verbose_name_plural = _(u"Educations")

    def __str__(self):
        return self.user.username


class AbstractEducationAttachment(models.Model):
    _UPLOAD_TO = 'files/educations'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    education = models.ForeignKey('person.Education', on_delete=models.CASCADE,
                                   related_name='education_attachments')

    title = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, blank=True)
    attach_type = models.CharField(max_length=255, editable=False)
    attach_file = models.FileField(upload_to=_UPLOAD_TO, max_length=500)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-create_date']
        verbose_name = _(u"Education Attachment")
        verbose_name_plural = _(u"Education Attachments")

    def __str__(self):
        return self.title
