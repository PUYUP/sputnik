import uuid
from dateutil import rrule

from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.utils.timezone import datetime
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.validators import non_python_keyword, identifier_validator
from apps.helpdesk.utils.constants import (
    CANAL_CHOICES, RECUR, RRULE_RECURRENCE_CHOICES, TEXT, OPEN, PRIORITY_CHOICES, MEDIUM, RRULE_WKST_CHOICES,
    RRULE_FREQ_CHOICES
)

MAX_ALLOWED_SCHEDULE = 6


class AbstractSchedule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='schedule')

    label = models.CharField(max_length=255)
    description = models.TextField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=1, null=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Schedule")
        verbose_name_plural = _("Schedules")
        constraints = [
            models.UniqueConstraint(fields=['user', 'label'], name='unique_user_label')
        ]

    def __str__(self):
        return '{0}'.format(self.label)

    def clean(self):
        # limited schedule each user
        if not self.pk and self.user:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            if c > MAX_ALLOWED_SCHEDULE:
                raise ValidationError({'user': _(u"Max %s schedule" % MAX_ALLOWED_SCHEDULE)})

    def save(self, *args, **kwargs):
        if self.user and not self.pk:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            self.sort_order = c + 1
        super().save(*args, **kwargs)

    @property
    def permalink(self):
        from django.urls import reverse
        return reverse('helpdesk_view:consultant:schedule_detail', kwargs={'uuid': self.uuid})

    @property
    def expertise(self):
        objs = self.schedule_expertise \
            .prefetch_related(Prefetch('expertise'), Prefetch('expertise__topic'), Prefetch('schedule')) \
            .select_related('expertise', 'schedule') \
            .values_list('expertise__topic__label', flat=True)
        return objs


class AbstractScheduleTerm(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    schedule = models.OneToOneField('helpdesk.Schedule', on_delete=models.CASCADE,
                                    related_name='schedule_term')

    dtstart = models.DateTimeField(default=datetime.now())
    dtuntil = models.DateTimeField(null=True, blank=True)
    tzid = models.CharField(max_length=255, default='UTC')
    freq = models.IntegerField(choices=RRULE_FREQ_CHOICES, default=rrule.WEEKLY)
    count = models.BigIntegerField(default=30)
    interval = models.BigIntegerField(default=1)
    wkst = models.CharField(choices=RRULE_WKST_CHOICES, default=str(rrule.FD), max_length=2,
                            validators=[non_python_keyword, identifier_validator])
    direction = models.CharField(choices=RRULE_RECURRENCE_CHOICES, default=RECUR, max_length=20)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-dtstart']
        verbose_name = _("Schedule Term")
        verbose_name_plural = _("Schedule Terms")

    def __str__(self):
        return '{0}'.format(self.dtstart)


class AbstractScheduleExpertise(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='schedule_expertise')
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='schedule_expertise')
    # Before user create schedule must complete the resume
    expertise = models.ForeignKey('resume.Expertise', on_delete=models.CASCADE,
                                  related_name='schedule_expertise')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Schedule Expertise")
        verbose_name_plural = _("Schedule Expertises")
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'expertise'], 
                name='unique_schedule_expertise'
            )
        ]

    def __str__(self):
        return self.expertise.topic.label

    @property
    def expertise_label(self):
        return self.expertise.topic.label


class AbstractSegment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='segment')
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='segment')

    canal = models.CharField(choices=CANAL_CHOICES, default=TEXT, max_length=25,
                             validators=[identifier_validator, non_python_keyword])
    open_hour = models.TimeField()
    close_hour = models.TimeField()
    quota = models.IntegerField(help_text=_("How many Issue allowed with status open"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Segment")
        verbose_name_plural = _("Segments")

    @property
    def is_open(self):
        # check segment allow new consultation or not by compare ':max_openend'
        # with consultations has opened status
        consultation_count = self.schedule.reservation.issue.consultation \
            .filter(status=OPEN).count()
        return self.max_opened > consultation_count

    def __str__(self):
        return '{0} from {1} to {2}'.format(self.schedule, self.open_hour, self.close_hour)


class AbstractSLA(models.Model):
    _ALLOC_TEXT = 10 # in replied
    _ALLOC_VOICE = 60 # in minutes
    _ALLOV_VIDEO = _ALLOC_VOICE

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='sla')
    segment = models.ForeignKey('helpdesk.Segment', on_delete=models.CASCADE,
                                related_name='sla')

    label = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    promise = models.TextField(help_text=_("What the user gets"))
    secret_content = models.TextField(help_text=_("Information only show to User has scheduled"),
                                      null=True, blank=True)
    grace_periode = models.IntegerField(help_text=_("In hours"))
    cost = models.BigIntegerField()
    allocation = models.IntegerField(null=True, help_text=_("If canal Text unit is replied, if other is minute"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-cost']
        verbose_name = _("SLA")
        verbose_name_plural = _("SLA's")

    def clean(self):
        if not self.allocation:
            raise ValidationError({'allocation': _(u"Can't empty")})
        
        if self.allocation <= 0:
            raise ValidationError({'allocation': _(u"Must larger than 0")})

    def save(self, *args, **kwargs):
        # fill label
        if not self.label:
            self.label = '{0} hours cost {1}'.format(self.grace_periode, self.cost)
        super().save(*args, **kwargs)

    def __str__(self):
        label = self.label
        if not label:
            label = '{0} ({1} hours) cost {2}'.format(self.label, self.grace_periode, self.cost)
        return label


class AbstractPriority(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='priority')
    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.CASCADE, related_name='priority')

    identifier = models.CharField(choices=PRIORITY_CHOICES, max_length=15, default=MEDIUM,
                                  validators=[non_python_keyword, identifier_validator])
    label = models.CharField(max_length=255)
    description = models.TextField(max_length=500, null=True, blank=True)
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
    _limit_ct = models.Q(app_label='helpdesk') & models.Q(model__in=['sla'])

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.CASCADE,
                            related_name='gift')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_ct,
                                     related_name='gift', null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Gift")
        verbose_name_plural = _("Gifts")

    def __str__(self):
        return self.sla.label
