from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.Meta.model(**attrs)
        instance.clean()
        return attrs


def month_validator(value):
    try:
        int(value)
    except ValueError:
        raise ValidationError(_("Only accept number"))

    if len(value) < 1:
        raise ValidationError(_("Month is 2 digit"))


def year_validator(value):
    try:
        int(value)
    except ValueError:
        raise ValidationError(_("Only accept number"))

    if len(value) < 4:
        raise ValidationError(_("Year is 4 digit"))
