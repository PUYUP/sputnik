import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractTopic(models.Model):
    """ie: PHP, JavaScript"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'master'
        ordering = ['-label']
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")
        constraints = [
            models.UniqueConstraint(fields=['label'], name='unique_topic_label')
        ]

    def __str__(self):
        return self.label
