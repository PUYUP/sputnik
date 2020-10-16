import uuid

from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from apps.helpdesk.utils.constants import (
    CANAL_CHOICES, TEXT, OPEN
)

MAX_ALLOWED_SCHEDULE = 6


class AbstractSchedule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='schedules')

    label = models.CharField(max_length=255)
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
        if self.user:
            c = self.__class__.objects.filter(user_id=self.user.id).count()
            if c > MAX_ALLOWED_SCHEDULE:
                raise ValidationError({'user': _(u"Max %s schedules" % MAX_ALLOWED_SCHEDULE)})

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
    def expertises(self):
        objs = self.schedule_expertises \
            .prefetch_related(Prefetch('expertise'), Prefetch('expertise__topic'), Prefetch('schedule')) \
            .select_related('expertise', 'schedule') \
            .values_list('expertise__topic__label', flat=True)
        return objs


class AbstractScheduleExpertise(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='schedule_expertises')
    # Before user create schedule must complete the resume
    expertise = models.ForeignKey('resume.Expertise', on_delete=models.CASCADE,
                                  related_name='schedule_expertises')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Schedule Expertise")
        verbose_name_plural = _("Schedule Expertises")
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'expertise'], name='unique_schedule_expertise')
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
                             related_name='segments', editable=False)
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='segments')

    canal = models.CharField(choices=CANAL_CHOICES, default=TEXT, max_length=25,
                             validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    open_hour = models.TimeField()
    close_hour = models.TimeField()
    max_opened = models.IntegerField(help_text=_("How many Issue allowed with status open"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Segment")
        verbose_name_plural = _("Segments")

    @property
    def is_open(self) -> bool:
        # check segment allow new issue or not by compare ':max_openend'
        # with issues has opened status
        issue_open_count = self.assigns.prefetch_related(Prefetch('issue')) \
            .select_related('issue') \
            .filter(issue__status=OPEN).count()
        return self.max_opened > issue_open_count

    def save(self, *args, **kwargs):
        self.user = self.schedule.user
        super().save(*args, **kwargs)

    def __str__(self):
        return '{0} from {1} to {2}'.format(self.schedule, self.open_hour, self.close_hour)


class AbstractSLA(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
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
