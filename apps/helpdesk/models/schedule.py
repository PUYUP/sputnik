import uuid
from dateutil import rrule

from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.generals import get_model
from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.helpdesk.utils.constants import (
    CANAL_CHOICES, TEXT, OPEN, WKST_CHOICES, FREQ_CHOICES
)


class AbstractSchedule(models.Model):
    # create schedule based to :Expertise
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='schedules')
    expertise = models.ManyToManyField('helpdesk.Expertise', related_name='schedules')

    label = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # RRULE
    # https://tools.ietf.org/html/rfc5545
    freq = models.IntegerField(choices=FREQ_CHOICES, default=rrule.WEEKLY)
    tzid = models.CharField(max_length=255, default='UTC',
                            help_text=_(u"If given, it must be a string that will be used when "
                                        "no TZID property is found in the parsed string. "
                                        "If it is not given, and the property is not found, 'UTC' will be used by default."))

    dtstart = models.DateTimeField(help_text=_(u"The recurrence start. Besides being the base for the recurrence"
                                               ", missing parameters in the final recurrence"
                                               "instances will also be extracted from this date. If not given,"
                                               "datetime.now() will be used"))

    dtuntil = models.DateTimeField(null=True, blank=True,
                                   help_text=_(u"If given, this must be a datetime instance, "
                                               "that will specify the limit of the recurrence. "
                                               "If a recurrence instance happens to be the same as the datetime instance "
                                               "given in the until argument, this will be the last occurrence."))

    count = models.BigIntegerField(default=30, help_text=_(u"How many occurrences will be generated."))
    interval = models.BigIntegerField(default=1, help_text=_(u"The interval between each freq iteration. "
                                                             "For example, when using freq.YEARLY, an interval of 2 means once every two years, "
                                                             "but with freq.HOURLY, it means once every two hours. The default interval is 1."))

    wkst = models.CharField(choices=WKST_CHOICES, default=str(rrule.MO), max_length=2,
                            validators=[non_python_keyword, IDENTIFIER_VALIDATOR],
                            help_text=_(u"The week start day. Must be one of the MO, TU, WE constants, or an integer, "
                                        "specifying the first day of the week. This will affect recurrences based on weekly periods. "
                                        "The default week start is MO."))

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-dtstart']
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        constraints = [
            models.UniqueConstraint(fields=['user', 'label'], name='unique_user_label'),
            models.UniqueConstraint(fields=['user', 'dtstart'], name='unique_user_dtstart')
        ]

    def __str__(self):
        return '{0}'.format(self.dtstart)

    def clean(self):
        # freq
        if self.freq not in dict(FREQ_CHOICES):
            raise ValidationError(_(u"Freq: '%s' not available." % (self.freq)))

        # wkst
        if self.wkst not in dict(WKST_CHOICES):
            raise ValidationError(_(u"Wkst: '%s' not available." % (self.wkst)))


class AbstractSegment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='segments', editable=False)
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='segments')

    canal = models.CharField(choices=CANAL_CHOICES, default=TEXT, max_length=25,
                             validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    open_hour = models.TimeField()
    close_hour = models.TimeField()
    max_opened = models.IntegerField(help_text=_("How many Ticket allowed with status open"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Segment")
        verbose_name_plural = _("Segments")

    @property
    def is_open(self) -> bool:
        # check segment allow new ticket or not by compare ':max_openend'
        # with tickets has opened status
        ticket_open_count = self.assigns.prefetch_related(Prefetch('ticket')) \
            .select_related('ticket') \
            .filter(ticket__status=OPEN).count()
        return self.max_opened > ticket_open_count

    def save(self, *args, **kwargs):
        self.user = self.schedule.user
        super().save(*args, **kwargs)

    def __str__(self):
        return '{0} from {1} to {2}'.format(self.schedule, self.open_hour, self.close_hour)


class AbstractSLA(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='slas', editable=False)
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='slas', editable=False)
    segment = models.ForeignKey('helpdesk.Segment', on_delete=models.CASCADE,
                                related_name='slas', null=True)

    label = models.CharField(max_length=255)
    summary = models.TextField(max_length=500, null=True, blank=True)
    promise = models.TextField(help_text=_("What the user gets"))
    secret_content = models.TextField(help_text=_("Information only show to User has scheduled"),
                                      null=True, blank=True)
    grace_periode = models.IntegerField(help_text=_("In hours"))
    cost = models.BigIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-cost']
        verbose_name = _("SLA")
        verbose_name_plural = _("SLA's")

    def save(self, *args, **kwargs):
        self.user = self.segment.user
        self.schedule = self.segment.schedule
        super().save(*args, **kwargs)

    def __str__(self):
        return '{0} ({1} hours) cost {2}'.format(self.label, self.grace_periode, self.cost)


class AbstractPriority(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='priorities')
    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.CASCADE,
                            related_name='priorities')

    label = models.CharField(max_length=255)
    summary = models.TextField(max_length=500, null=True, blank=True)
    cost = models.BigIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-cost']
        verbose_name = _("Priority")
        verbose_name_plural = _("Priorities")

    def __str__(self):
        return '{0} cost {1}'.format(self.label, self.cost)


class AbstractGift(models.Model):
    _limit_content_type = models.Q(app_label='helpdesk') & models.Q(model__in=['sla'])

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.CASCADE,
                            related_name='gifts')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_content_type,
                                     related_name='gifts', null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    material = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")

    def __str__(self):
        return self.sla.label
