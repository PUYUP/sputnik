"""
Schedule has one schedule_term and schedule_term has many rule
Rules separate two mode: inclusion and exclusion
- inclusion: mean "show it on schedule_term"
- exclusion: mean "hide it on schedule_term"

Example;
- exclusion: remove date from schedule_term, maybe for self holiday
- inclusion: add date to schedule_term, maybe a special day
"""

import uuid

from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from utils.generals import get_model
from utils.validators import non_python_keyword, identifier_validator
from apps.helpdesk.utils.constants import (
    INCLUSION, RRULE_MODE_CHOICES,
    RRULE_IDENTIFIER_CHOICES, RRULE_TYPE_CHOICES,
    VARCHAR, RRULE_RECURRENCE_CHOICES, RECUR
)


class AbstractRule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='rule')
    schedule_term = models.ForeignKey('helpdesk.ScheduleTerm', on_delete=models.CASCADE,
                                      related_name='rule')
    identifier = models.SlugField(choices=RRULE_IDENTIFIER_CHOICES, max_length=128,
                                  verbose_name=_("Identifier"),
                                  validators=[identifier_validator, non_python_keyword])
    mode = models.CharField(default=INCLUSION, choices=RRULE_MODE_CHOICES, max_length=25,
                            validators=[non_python_keyword, identifier_validator])
    type = models.CharField(choices=RRULE_TYPE_CHOICES, default=VARCHAR, max_length=20)
    direction = models.CharField(choices=RRULE_RECURRENCE_CHOICES, default=RECUR, max_length=20)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("ScheduleTerm Rule")
        verbose_name_plural = _("ScheduleTerm Rules")
        constraints = [
            models.UniqueConstraint(
                fields=['schedule_term', 'mode', 'identifier', 'direction'], 
                name='unique_schedule_term_rule'
            )
        ]

    def __str__(self):
        return '{0}'.format(self.get_identifier_display())


class AbstractRuleValue(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    rule = models.ForeignKey('helpdesk.Rule', on_delete=models.CASCADE,
                             related_name='rule_value')
    schedule_term = models.ForeignKey('helpdesk.ScheduleTerm', on_delete=models.CASCADE,
                                      related_name='rule_value', editable=False)

    value_varchar = models.CharField(_('Text'), blank=True, null=True, max_length=255)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(_('DateTime'), blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['create_date']
        verbose_name = _("ScheduleTerm Rule Value")
        verbose_name_plural = _("ScheduleTerm Rule Values")
        constraints = [
            models.UniqueConstraint(
                fields=['rule', 'value_varchar'], 
                name='unique_rule_value_varchar'
            ),
            models.UniqueConstraint(
                fields=['rule', 'value_integer'], 
                name='unique_rule_value_integer'
            ),
            models.UniqueConstraint(
                fields=['rule', 'value_datetime'], 
                name='unique_rule_value_datetime'
            )
        ]

    def save(self, *args, **kwargs):
        self.schedule_term = self.rule.schedule_term
        super().save(*args, **kwargs)

    def __str__(self):
        return self.summary()

    def clean(self):
        value_field = 'value_%s' % self.rule.type
        value = getattr(self, value_field)
        self.validate_value_type(value, value_field)

    def validate_value_type(self, value, field):
        _validator_func = '_validate_%s' % field

        try:
            validator = getattr(self, _validator_func)
            validator(value)
        except AttributeError:
            pass

    # start validator
    # each validator depend to Rule type
    def _validate_value_varchar(self, value):
        if not value:
            raise ValidationError({'value_varchar': _("Can't empty")})

    def _validate_value_integer(self, value):
        if not value:
            raise ValidationError({'value_integer': _("Can't empty")})

    def _validate_value_datetime(self, value):
        if not value:
            raise ValidationError({'value_datetime': _("Can't empty")})

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.rule.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = 'value_%s' % self.rule.type
        setattr(self, attr_name, new_value)
        return

    value = property(_get_value, _set_value)

    def summary(self):
        """
        Gets a string representation of both the rule and it's value,
        used e.g in schedule summaries.
        """
        return "%s: %s" % (self.rule.identifier, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the rule's value. To customise
        e.g. image rule values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.rule.type
        return getattr(self, property_name, self.value)
