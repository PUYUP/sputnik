import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractScope(models.Model):
    """ie: Web Developer"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)
    subject = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-subject']
        verbose_name = _("Scope")
        verbose_name_plural = _("Scopes")
        constraints = [
            models.UniqueConstraint(fields=['subject'], name='unique_scope_subject')
        ]

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class AbstractTopic(models.Model):
    """ie: PHP, JavaScript"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    scope = models.ForeignKey('helpdesk.Scope', on_delete=models.SET_NULL,
                              null=True, related_name='topics',
                              limit_choices_to={'is_active': True})
    subject = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-subject']
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")
        constraints = [
            models.UniqueConstraint(fields=['subject'], name='unique_topic_subject')
        ]

    def __str__(self):
        return self.subject
