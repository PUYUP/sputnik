import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.resume.utils.constants import EDUCATION_STATUS, DRAFT


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
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _(u"Education")
        verbose_name_plural = _(u"Educations")

    def __str__(self):
        return self.user.username
