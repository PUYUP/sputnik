import uuid
import os

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError

ALLOWED_EXTENSIONS = ['.jpeg', '.jpg', '.png', '.pdf', '.docx']


class AbstractAttachment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='helpdesk_attachment')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to={'app_label': 'helpdesk'},
                                     related_name='helpdesk_attachment')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, editable=False)
    file = models.FileField(max_length=500)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _(u"Attachment")
        verbose_name_plural = _(u"Attachments")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        if not self.label:
            self.label = self.file.name

        super().save(*args, **kwargs)

    def clean(self):
        if self.object_id:
            ct_model = self.content_type.model_class()
            try:
                ct_model.objects.get(id=self.object_id)
            except ObjectDoesNotExist:
                raise ValidationError(
                    {'object_id': _('Invalid pk "'+str(self.object_id)+'" - object does not exist.')}
                )

        if self.file:
            _name, ext = os.path.splitext(self.file.name)
            fsize = self.file.size / 1000

            if fsize > 5000:
                raise ValidationError({'file': _("Ukuran file maksimal 5 MB")})

            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError({'file': _("Jenis file tidak diperbolehkan")})
