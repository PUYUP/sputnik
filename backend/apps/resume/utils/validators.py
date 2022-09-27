from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


def month_validator(value):
    if value:
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Only accept number"))

        if not isinstance(value, str):
            value = str(value)

        if len(value) < 1:
            raise ValidationError(_("Month is 2 digit"))


def year_validator(value):
    if value:
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Only accept number"))

        if not isinstance(value, str):
            value = str(value)

        if len(value) < 4:
            raise ValidationError(_("Year is 4 digit"))
