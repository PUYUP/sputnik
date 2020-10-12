import uuid
from datetime import date, datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from utils.generals import get_model
from utils.constants import MONTH_CHOICES
from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.helpdesk.utils.constants import (
    VARCHAR, ATTRIBUTE_TYPE_CHOICES, ATTRIBUTE_CHOICES, BOOLEAN,
    BYHOUR, BYMINUTE, BYSECOND, WKST_CHOICES
)

_limit_content_type = models.Q(app_label='helpdesk')


class AttributeValueManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        # validate all fields
        for item in objs:
            field = item.attribute.type
            field_value = 'value_%s' % field
            value = getattr(item, field_value)
            item.validate_value(value)

        return super(AttributeValueManager, self).bulk_create(objs, **kwargs)  


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type
    For example, Language
    """
    name = models.CharField(_('Name'), max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    group = models.ForeignKey(
        'helpdesk.AttributeOptionGroup',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    def __str__(self):
        return self.option

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        unique_together = ('group', 'option')
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')


class AbstractAttribute(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    # this same as Entity (Schedule, Segment, others)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_content_type,
                                     related_name='attributes')

    label = models.CharField(verbose_name=_("Label"), max_length=255,
                             null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    identifier = models.SlugField(
        choices=ATTRIBUTE_CHOICES,
        verbose_name=_("Identifier"),
        max_length=128,
        validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    type = models.CharField(
        choices=ATTRIBUTE_TYPE_CHOICES, default=VARCHAR,
        max_length=20, verbose_name=_("Type"))

    option_group = models.ForeignKey(
        'helpdesk.AttributeOptionGroup',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='attributes',
        verbose_name=_("Option Group"),
        help_text=_('Select an option group if using type "Option" or "Multi Option"'))
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Attribute")
        verbose_name_plural = _("Attributes")
        constraints = [
            models.UniqueConstraint(fields=['content_type', 'label'], name='unique_content_type_label')
        ]

    def __str__(self):
        return self.label

    @property
    def is_option(self):
        return self.type == self.OPTION

    @property
    def is_multi_option(self):
        return self.type == self.MULTI_OPTION

    def clean(self):
        if self.type == BOOLEAN and self.required:
            raise ValidationError({'type': _("Boolean attribute should not be required")})

    def _set_multi_option(self, value_obj, value):
        # ManyToMany fields are handled separately
        if value is None:
            value_obj.delete()
            return
        try:
            count = value.count()
        except (AttributeError, TypeError):
            count = len(value)
        if count == 0:
            value_obj.delete()
        else:
            value_obj.value = value
            value_obj.save()

    def _set_value(self, value_obj, deleted=False, created=True):
        # if current_value set to None or empty, delete object
        if deleted and not created:
            value_obj.delete()
            return

    # set attribute value to content_object (entity object, eg: Schedule)
    # :content_object must a single object
    # :content_object mean as AttributeValue
    def set_value(self, content_object, current_value, update_value=None, deleted=False):   # noqa: C901 too complex
        """ HELP ME!
        # get the attribute itself
        :attribute = Attribute.object.get(id=1)

        # get the object want to set value
        :content_object = Schedule.objects.get(id=1)

        # set new value
        attribute.set_value(content_object, 'new_value')

        # update old value
        attribute.set_value(content_object, 'new_value', 'something new here')

        # delete value
        attribute.set_value(content_object, is_delete=True)
        """
        AttributeValue = get_model('helpdesk', 'AttributeValue')
        ct = ContentType.objects.get_for_model(content_object, for_concrete_model=False)

        field = 'value_%s' % self.type
        field_value = {field: current_value}
        defaults = {field: update_value if update_value else current_value}

        # if value not exist create
        # if exist update
        value_obj, created = AttributeValue.objects \
            .update_or_create(attribute=self, object_id=content_object.id, content_type=ct,
                              **field_value, defaults=defaults)

        if self.is_multi_option:
            self._set_multi_option(value_obj, current_value)
        else:
            self._set_value(value_obj, deleted=deleted, created=created)

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.type)
        validator(value)

    # Validators

    def _validate_varchar(self, value):
        if not isinstance(value, str):
            raise ValidationError(_("Must be str"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError(
                _("Must be a list or AttributeOption queryset"))
        # Validate each value as if it were an option
        # Pass in valid_values so that the DB isn't hit multiple times per iteration
        valid_values = self.option_group.options.values_list(
            'option', flat=True)
        for value in values:
            self._validate_option(value, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model('helpdesk', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))
        if valid_values is None:
            valid_values = self.option_group.options.values_list(
                'option', flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                _("%(enum)s is not a valid choice for %(attr)s") %
                {'enum': value, 'attr': self})


class AbstractAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`Schedule <.AbstractSchedule>` and
    :py:class:`Attribute <.AbstractAttribute>`  This specifies the value of the attribute for
    a particular schedule
    For example: ``number_of_pages = 295``
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    attribute = models.ForeignKey('helpdesk.Attribute', on_delete=models.CASCADE,
                                  related_name='attribute_values', verbose_name=_("Attribute"))

    # attribute content type
    attribute_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                               limit_choices_to=_limit_content_type,
                                               related_name='attribute_values',
                                               editable=False)

    # object from entity egg: Schedule object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_content_type)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    value_varchar = models.CharField(_('Text'), blank=True, null=True, max_length=255)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.BooleanField(_('Boolean'), blank=True, null=True, db_index=True)
    value_date = models.DateField(_('Date'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(_('DateTime'), blank=True, null=True, db_index=True)

    objects = AttributeValueManager()

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        verbose_name = _('Attribute Value')
        verbose_name_plural = _('Attribute Values')
        constraints = [
            models.UniqueConstraint(
                fields=['attribute', 'value_varchar'], 
                name='unique_attribute_value_varchar'
            ),
            models.UniqueConstraint(
                fields=['attribute', 'value_integer'], 
                name='unique_attribute_value_integer'
            ),
            models.UniqueConstraint(
                fields=['attribute', 'value_boolean'], 
                name='unique_attribute_value_boolean'
            ),
            models.UniqueConstraint(
                fields=['attribute', 'value_date'], 
                name='unique_attribute_value_date'
            ),
            models.UniqueConstraint(
                fields=['attribute', 'value_datetime'], 
                name='unique_attribute_value_datetime'
            )
        ]

    def __str__(self):
        return self.summary()

    def setnull_unused_value(self, exclude_type=None):
        # setnull except type
        if exclude_type:
            type_list = list(dict(ATTRIBUTE_TYPE_CHOICES).keys())
            type_list.remove(exclude_type)

            for t in type_list:
                attr_name = 'value_%s' % t
                setattr(self, attr_name, None)

    def save(self, *args, **kwargs):
        if self.attribute:
            self.attribute_content_type = self.attribute.content_type

        # setnull unused field value
        self.setnull_unused_value(self.attribute.type)
        
        # validation
        self.clean()

        # saved!
        super().save(*args, **kwargs)

    def clean(self):
        if self.attribute:
            value = getattr(self, 'value_%s' % self.attribute.type)

            # :schedule validator
            if self.attribute_content_type.model == 'schedule':
                if (
                    not value 
                    and (
                        isinstance(value, int)
                        and (
                            (self.attribute.type != BYHOUR and value < 0)
                            or (self.attribute.type != BYMINUTE and value < 0) 
                            or (self.attribute.type != BYSECOND and value < 0)
                        )
                    )
                ):
                    raise ValidationError({value: _("%s can't empty" % (self.attribute.get_type_display()))})

            self.validate_value(value)

    def validate_value(self, value):
        # general validator (varchar, int, others)
        _validator_func = '_validate_%s' % self.attribute.type

        # :schedule validator
        if self.attribute_content_type.model == 'schedule':
            _validator_func = '_rrule_%s' % self.attribute.identifier

        validator = getattr(self, _validator_func)
        validator(value)

    """#################
    General Validators
    #################"""
    def _validate_varchar(self, value):
        if not isinstance(value, str):
            raise ValidationError({'value_varchar': _("Must be str")})

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'value_integer': _("Must be an integer")})

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError({'value_date': _("Must be a date or datetime")})

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError({'value_datetime': _("Must be a datetime")})

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError({'value_boolean': _("Must be a boolean")})

    """#################
    RRULE Validators
    #################"""
    def _rrule_byweekday(self, value):
        if value.isdigit():
            raise ValidationError({'byweekday': _("Must be string")})

        if value not in dict(WKST_CHOICES) or not value.isupper():
            keys = list(dict(WKST_CHOICES).keys())
            raise ValidationError({'byweekday': _("Value %s not available. Valid choices is %s" % (str(value), ', '.join(keys)))})

    def _rrule_bymonth(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'bymonth': _("Must be an integer")})

        if value not in dict(MONTH_CHOICES):
            keys = list(dict(MONTH_CHOICES).keys())
            raise ValidationError({'bymonth': _("Value %s not available. Valid choices is %s" % (str(value), ', '.join(str(v) for v in keys)))})

    def _rrule_bysetpos(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'bysetpos': _("Must be an integer")})

    def _rrule_bymonthday(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'bymonthday': _("Must be an integer")})

        if value < 1 or value == 0:
            raise ValidationError({'bymonthday': _("Must larger than 0")})

        if value not in range(1, 32):
            raise ValidationError({'bymonthday': _("Out of range. Accept 1 to 31")})

    def _rrule_byyearday(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'byyearday': _("Must be an integer")})

        if value < 1 or value == 0:
            raise ValidationError({'byyearday': _("Must larger than 0")})

        if value not in range(1, 366):
            raise ValidationError({'byyearday': _("Out of range. Accept 1 to 365")})

    def _rrule_byweekno(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'byweekno': _("Must be an integer")})

        if value < 1 or value == 0:
            raise ValidationError({'byweekno': _("Must larger than 0")})

        if value not in range(1, 53):
            raise ValidationError({'byweekno': _("Out of range. Accept 1 to 52")})

    def _rrule_byhour(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'byhour': _("Must be an integer")})

        if value < 0:
            raise ValidationError({'byhour': _("Must larger than -1")})

        if value not in range(0, 24):
            raise ValidationError({'byhour': _("Out of range. Accept 0 to 23")})

    def _rrule_byminute(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'byminute': _("Must be an integer")})

        if value < 0:
            raise ValidationError({'byminute': _("Must larger than -1")})

        if value not in range(0, 60):
            raise ValidationError({'byminute': _("Out of range. Accept 0 to 59")})

    def _rrule_bysecond(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError({'bysecond': _("Must be an integer")})

        if value < 0:
            raise ValidationError({'bysecond': _("Must larger than -1")})

        if value not in range(0, 60):
            raise ValidationError({'bysecond': _("Out of range. Accept 0 to 59")})

    def _rrule_exclude_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError({'exclude_date': _("Must be a date or datetime")})

    def _rrule_exclude_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError({'exclude_date': _("Must be a datetime")})

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, current_value):
        attr_name = 'value_%s' % self.attribute.type
        setattr(self, attr_name, current_value)
        return

    field_value = property(_get_value, _set_value)

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in schedule summaries.
        """
        return "%s: %s" % (self.attribute.label, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.attribute.type
        return getattr(self, property_name, self.field_value)

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a ``_image_as_html`` property and
        return e.g. an ``<img>`` tag.  Defaults to the ``_as_text``
        representation.
        """
        property_name = '_%s_as_html' % self.attribute.type
        return getattr(self, property_name, self.value_as_text)
