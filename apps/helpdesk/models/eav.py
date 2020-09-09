import uuid
from datetime import date, datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from utils.generals import get_model
from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.helpdesk.utils.constants import (
    VARCHAR, ATTRIBUTE_TYPE_CHOICES, ATTRIBUTE_CHOICES, BOOLEAN,
    BYHOUR, BYMINUTE, BYSECOND, WKST_CHOICES, MONTH_CHOICES
)

_limit_content_type = models.Q(app_label='helpdesk')


class AbstractAttribute(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
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
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit")),
            non_python_keyword
        ])

    type = models.CharField(
        choices=ATTRIBUTE_TYPE_CHOICES, default=VARCHAR,
        max_length=20, verbose_name=_("Type"))
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

    def clean(self):
        if self.type == BOOLEAN and self.required:
            raise ValidationError(_("Boolean attribute should not be required"))

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    # set attribute value to content_object (entity object, eg: Schedule)
    # :content_object must a single object
    def save_value(self, content_object, value):   # noqa: C901 too complex
        AttributeValue = get_model('helpdesk', 'AttributeValue')
        try:
            value_obj = content_object.attribute_values.get(attribute=self)
        except AttributeValue.DoesNotExist:
            value_obj = AttributeValue.objects.create(content_object=content_object, attribute=self)

        self._save_value(value_obj, value)

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


class AbstractAttributeValue(models.Model):
    """
    The "through" model for the m2m relationship between :py:class:`Schedule <.AbstractSchedule>` and
    :py:class:`Attribute <.AbstractAttribute>`  This specifies the value of the attribute for
    a particular schedule
    For example: ``number_of_pages = 295``
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    attribute = models.ForeignKey('helpdesk.Attribute', on_delete=models.CASCADE,
                                  related_name='attribute_values', verbose_name=_("Attribute"))

    # attribute content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_content_type,
                                     related_name='attribute_values',
                                     editable=False)
    
    # object from entity egg: Schedule object
    value_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                           limit_choices_to=_limit_content_type,
                                           related_name='attribute_value_types')
    value_object_id = models.PositiveIntegerField()
    value_content_object = GenericForeignKey('value_content_type', 'value_object_id')

    value_varchar = models.CharField(_('Text'), blank=True, null=True, max_length=255)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.BooleanField(_('Boolean'), blank=True, null=True, db_index=True)
    value_date = models.DateField(_('Date'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(_('DateTime'), blank=True, null=True, db_index=True)

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
            self.content_type = self.attribute.content_type

        # setnull unused field value
        self.setnull_unused_value(self.attribute.type)

        super().save(*args, **kwargs)

    def clean(self):
        if self.attribute:
            value = getattr(self, 'value_%s' % self.attribute.type)

            # :schedule validator
            if self.content_type.model == 'schedule':
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
                    raise ValidationError(_("%s can't empty" % (self.attribute.get_type_display())))

            self.validate_value(value)

    def validate_value(self, value):
        # general validator (varchar, int, others)
        _validator_func = '_validate_%s' % self.attribute.type

        # :schedule validator
        if self.content_type.model == 'schedule':
            _validator_func = '_rrule_%s' % self.attribute.identifier

        validator = getattr(self, _validator_func)
        validator(value)

    """#################
    General Validators
    #################"""
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

    """#################
    RRULE Validators
    #################"""
    def _rrule_byweekday(self, value):
        if value.isdigit():
            raise ValidationError(_("Must be string"))

        if value not in dict(WKST_CHOICES) or not value.isupper():
            keys = list(dict(WKST_CHOICES).keys())
            raise ValidationError(_("Not available. Use one of %s" % (', '.join(keys))))

    def _rrule_bymonth(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value not in dict(MONTH_CHOICES):
            keys = list(dict(MONTH_CHOICES).keys())
            raise ValidationError(_("Not available. Use one of %s" % (', '.join(str(v) for v in keys))))

    def _rrule_bysetpos(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _rrule_bymonthday(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 1 or value == 0:
            raise ValidationError(_("Must larger than 0"))

        if value not in range(1, 32):
            raise ValidationError(_("Out of range. Accept 1 to 31"))

    def _rrule_byyearday(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 1 or value == 0:
            raise ValidationError(_("Must larger than 0"))

        if value not in range(1, 366):
            raise ValidationError(_("Out of range. Accept 1 to 365"))

    def _rrule_byweekno(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 1 or value == 0:
            raise ValidationError(_("Must larger than 0"))

        if value not in range(1, 53):
            raise ValidationError(_("Out of range. Accept 1 to 52"))

    def _rrule_byhour(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 0:
            raise ValidationError(_("Must larger than -1"))

        if value not in range(0, 24):
            raise ValidationError(_("Out of range. Accept 0 to 23"))

    def _rrule_byminute(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 0:
            raise ValidationError(_("Must larger than -1"))

        if value not in range(0, 60):
            raise ValidationError(_("Out of range. Accept 0 to 59"))

    def _rrule_bysecond(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

        if value < 0:
            raise ValidationError(_("Must larger than -1"))

        if value not in range(0, 60):
            raise ValidationError(_("Out of range. Accept 0 to 59"))

    def _rrule_exclude_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _rrule_exclude_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = 'value_%s' % self.attribute.type
        setattr(self, attr_name, new_value)
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
