import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AbstractScope(models.Model):
    """ie: Web Developer"""
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
        verbose_name = _("Scope")
        verbose_name_plural = _("Scopes")
        constraints = [
            models.UniqueConstraint(fields=['label'], name='unique_scope_label')
        ]

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class AbstractSkill(models.Model):
    """ie: PHP, JavaScript"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    scope = models.ForeignKey('master.Scope', on_delete=models.SET_NULL,
                              null=True, related_name='skills',
                              limit_choices_to={'is_active': True})
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'master'
        ordering = ['-label']
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        constraints = [
            models.UniqueConstraint(fields=['label'], name='unique_skill_label')
        ]

    def __str__(self):
        return self.label
