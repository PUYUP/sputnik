import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from apps.resume.utils.validators import year_validator
from apps.resume.utils.constants import EDUCATION_STATUS, DRAFT


class AbstractEducation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='education')
    attachments = GenericRelation('resume.Attachment', content_type_field='content_type',
                                  object_id_field='object_id', related_query_name='education')

    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, null=True, blank=True)
    study = models.CharField(max_length=255, null=True, blank=True)
    start_year = models.CharField(max_length=4, null=True, blank=True,
                                  validators=[year_validator])
    end_year = models.CharField(max_length=4, null=True, blank=True,
                                validators=[year_validator])
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


    def save(self, *args, **kwargs):
        if self.user and not self.pk:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            self.sort_order = c + 1
        super().save(*args, **kwargs)
