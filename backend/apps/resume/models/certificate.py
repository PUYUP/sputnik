import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation

from apps.resume.utils.constants import CERTIFICATE_STATUS, DRAFT


class AbstractCertificate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='certificates')
    attachments = GenericRelation('resume.Attachment', content_type_field='content_type',
                                  object_id_field='object_id', related_query_name='certificate')

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.CharField(max_length=255, null=True, blank=True)
    has_expiration = models.BooleanField(default=False)
    issued = models.DateField(auto_now_add=False)
    expired = models.DateField(auto_now_add=False, null=True, blank=True)
    credential_id = models.CharField(null=True, blank=True, max_length=255)
    credential_url = models.URLField(null=True, blank=True, max_length=500)
    sort_order = models.IntegerField(default=1, null=True)
    status = models.CharField(choices=CERTIFICATE_STATUS, max_length=15,
                              default=DRAFT, null=True)

    class Meta:
        abstract = True
        app_label = 'resume'
        ordering = ['-create_date']
        verbose_name = _(u"Certificate")
        verbose_name_plural = _(u"Certificates")

    def __str__(self):
        return self.user.username

    def clean(self, *args, **kwargs):
        if self.has_expiration:
            if not self.expired:
                raise ValidationError({'expired': _("Expired required")})

    def save(self, *args, **kwargs):
        if self.user and not self.pk:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            self.sort_order = c + 1
        super().save(*args, **kwargs)
