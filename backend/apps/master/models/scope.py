import uuid

from django.db import models
from django.db.models.fields import related
from django.utils.translation import ugettext_lazy as _


class AbstractScope(models.Model):
    """ie: Web Developer"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    topics = models.ManyToManyField('master.Topic', related_name='scope')
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'master'
        ordering = ['-label']
        verbose_name = _("Scope")
        verbose_name_plural = _("Scopes")
        constraints = [
            models.UniqueConstraint(fields=['label'], name='unique_scope_label')
        ]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
