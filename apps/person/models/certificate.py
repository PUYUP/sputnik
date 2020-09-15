import uuid
import os

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template.defaultfilters import slugify

from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.person.utils.constants import (
    EMPLOYMENT_CHOICES,
    CERTIFICATE_STATUS,
    DRAFT
)


class AbstractCertificate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='certificates')

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.CharField(max_length=255, null=True, blank=True)
    issued = models.DateField(auto_now_add=False)
    expired = models.DateField(auto_now_add=False, null=True, blank=True)
    sort_order = models.IntegerField(default=1, null=True)
    status = models.CharField(choices=CERTIFICATE_STATUS, max_length=15,
                              default=DRAFT, null=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-create_date']
        verbose_name = _(u"Certificate")
        verbose_name_plural = _(u"Certificates")

    def __str__(self):
        return self.user.username


class AbstractCertificateAttachment(models.Model):
    _UPLOAD_TO = 'files/certificates'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    certificate = models.ForeignKey('person.Certificate', on_delete=models.CASCADE,
                                    related_name='certificate_attachments')

    title = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, blank=True)
    attach_type = models.CharField(max_length=255, editable=False)
    attach_file = models.FileField(upload_to=_UPLOAD_TO, max_length=500)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-create_date']
        verbose_name = _(u"Certificate Attachment")
        verbose_name_plural = _(u"Certificate Attachments")

    def __str__(self):
        return self.title
