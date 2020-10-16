"""
Schedule has one recurrence and recurrence has many rules
Rules separate two mode: inclusion and exclusion
- inclusion: mean "show it on recurrence"
- exclusion: mean "hide it on recurrence"

Example;
- exclusion: remove date from recurrence, maybe for self holiday
- inclusion: add date to recurrence, maybe a special day
"""

import uuid
from dateutil import rrule

from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import datetime
from django.core.exceptions import ValidationError

from utils.generals import get_model
from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.helpdesk.utils.constants import (
    INCLUSION, RRULE_FREQ_CHOICES, RRULE_MODE_CHOICES, RRULE_WKST_CHOICES,
    RRULE_IDENTIFIER_CHOICES, RRULE_TYPE_CHOICES,
    VARCHAR
)


class AbstractRecurrence(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    schedule = models.OneToOneField('helpdesk.Schedule', on_delete=models.CASCADE,
                                    related_name='recurrence')

    dtstart = models.DateTimeField(default=datetime.now())
    dtuntil = models.DateTimeField(null=True, blank=True)
    tzid = models.CharField(max_length=255, default='UTC')
    freq = models.IntegerField(choices=RRULE_FREQ_CHOICES, default=rrule.WEEKLY)
    count = models.BigIntegerField(default=30)
    interval = models.BigIntegerField(default=1)
    wkst = models.CharField(choices=RRULE_WKST_CHOICES, default=str(rrule.FD), max_length=2,
                            validators=[non_python_keyword, IDENTIFIER_VALIDATOR])

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-dtstart']
        verbose_name = _("Recurrence")
        verbose_name_plural = _("Recurrences")

    def __str__(self):
        return '{0}'.format(self.dtstart)


class AbstractRule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    recurrence = models.ForeignKey('helpdesk.Recurrence', on_delete=models.CASCADE,
                                   related_name='rules')

    identifier = models.SlugField(choices=RRULE_IDENTIFIER_CHOICES,
                                  verbose_name=_("Identifier"),
                                  max_length=128,
                                  validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    mode = models.CharField(default=INCLUSION, choices=RRULE_MODE_CHOICES, max_length=25,
                            validators=[non_python_keyword, IDENTIFIER_VALIDATOR])
    type = models.CharField(choices=RRULE_TYPE_CHOICES, default=VARCHAR,
                            max_length=20, verbose_name=_("Type"))

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Recurrence Rule")
        verbose_name_plural = _("Recurrence Rules")
        constraints = [
            models.UniqueConstraint(
                fields=['recurrence', 'mode', 'type', 'identifier'], 
                name='unique_recurrence_rule'
            )
        ]

    def __str__(self):
        return '{0}'.format(self.get_identifier_display())

    def save_values(self, values=list(dict())):
        """
        values format;
            [
                {'value': 'string', 'new_value': 'string'},
                {'value': 'string', 'new_value': 'string'}
            ]
        """
        RuleValue = get_model('helpdesk', 'RuleValue')
    
        sets = list()
        updates = list()
        value_type = 'value_%s' % self.type
   
        for v in values:
            sets.append(v.get('value', ''))
            updates.append(v.get('new_value', ''))

        # check value saved by filter out from database
        value_in = {'%s__in' % value_type: sets}
        saved_values = self.recurrence.rule_values \
            .filter(rule__mode=self.mode, rule__identifier=self.identifier, **value_in)
        saved_values_list = saved_values.values_list(value_type, flat=True)

        # compare current values with new_value
        unsaved_values = list(set(sets) - set(list(saved_values_list)))

        # update values
        if saved_values:
            update_values = list()
            for v in saved_values:
                # check value same
                old_value = getattr(v, value_type)
                item = list(filter(lambda x: x['value'] == old_value, values))
                if item:
                    new_value = item[0].get('new_value', '')
                    if new_value:
                        setattr(v, value_type, new_value)
                        update_values.append(v)

            if update_values:
                try:
                    RuleValue.objects.bulk_update(update_values, [value_type])
                except (IntegrityError, Exception) as e:
                    raise ValidationError(repr(e))

        # create new values
        if unsaved_values:
            create_values = list()
            for v in unsaved_values:
                field = {value_type: v}
                v_obj = RuleValue(rule=self, recurrence=self.recurrence, **field)
                create_values.append(v_obj)

            if create_values:
                try:
                    RuleValue.objects.bulk_create(create_values, ignore_conflicts=False)
                except (IntegrityError, Exception) as e:
                    raise ValidationError(repr(e))


class AbstractRuleValue(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    rule = models.ForeignKey('helpdesk.Rule', on_delete=models.CASCADE,
                             related_name='rule_values')
    recurrence = models.ForeignKey('helpdesk.Recurrence', on_delete=models.CASCADE,
                                   related_name='rule_values', editable=False)

    value_varchar = models.CharField(_('Text'), blank=True, null=True, max_length=255)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(_('DateTime'), blank=True, null=True, db_index=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['create_date']
        verbose_name = _("Recurrence Rule Value")
        verbose_name_plural = _("Recurrence Rule Values")
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
        self.recurrence = self.rule.recurrence
        super().save(*args, **kwargs)

    def __str__(self):
        return self.summary()

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