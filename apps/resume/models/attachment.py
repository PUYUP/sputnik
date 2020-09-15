import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AbstractAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to={'app_label': 'resume'},
                                     related_name='attachment_ct')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    label = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True, blank=True)
    attach_type = models.CharField(max_length=255, editable=False)
    attach_file = models.FileField(max_length=500)

    class Meta:
        abstract = True
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _(u"Attachment")
        verbose_name_plural = _(u"Attachments")

    def __str__(self):
        return self.label
