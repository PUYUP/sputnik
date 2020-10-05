import uuid

from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from utils.validators import non_python_keyword, IDENTIFIER_VALIDATOR
from utils.generals import random_string
from apps.helpdesk.utils.constants import (
    ISSUE_STATUS, OPEN,
    CLASSIFY_CHOICES,
    ASSIGN_STATUS, WAITING, ACCEPT,
    EVENT_CHOICES
)


class AbstractIssue(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)
    change_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='issues')
    skill = models.ManyToManyField('master.Skill', related_name='issues',
                                   limit_choices_to={'is_active': True})

    number = models.CharField(max_length=255, editable=False)
    status = models.CharField(choices=ISSUE_STATUS, default=OPEN, max_length=25,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    # if :consultant give a respond at first time change this to True
    is_responded = models.BooleanField(default=False)
    responded_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.pk:
            number = random_string(8)
            unique = False
            while not unique:
                exist = self.__class__.objects.filter(number=number).exists()
                if not exist:
                    unique = True
                else:
                    number = random_string(8)
            self.number = number
        super().save(*args, **kwargs)


class AbstractAssign(models.Model):
    """One :issue only assigned to one :consultant
    IMPORTANT! the :assign has attribute name :extra_cost
    with that attribute allow client add more cost for the issue"""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    # who create the Assign
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='assigns', editable=False)
    # a selected issue
    issue = models.ForeignKey('helpdesk.Issue', on_delete=models.CASCADE,
                              related_name='assigns')
    # target to Consultant
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='assign_consultants')

    # Consultant Schedule
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.SET_NULL,
                                 related_name='assigns', null=True, editable=False)
    segment = models.ForeignKey('helpdesk.Segment', on_delete=models.SET_NULL,
                                related_name='assigns', null=True)

    # start cost calculation
    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.SET_NULL,
                            related_name='assigns', null=True)
    priority = models.ForeignKey('helpdesk.Priority', on_delete=models.SET_NULL,
                                 related_name='assigns', null=True)

    # available value: accept, reject, cancel, waiting
    # client anytime can change :status if :status is waiting
    # maybe client want to assign :issue to another :consultant
    status = models.CharField(choices=ASSIGN_STATUS, default=WAITING, max_length=25,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Assign")
        verbose_name_plural = _("Assigns")
        constraints = [
            models.UniqueConstraint(
                fields=['issue', 'consultant'],
                condition=models.Q(status=ACCEPT),
                name='unique_issue_consultant'
            ),
        ]

    def __str__(self):
        return self.issue.number

    def save(self, *args, **kwargs):
        self.user = self.issue.user
        self.schedule = self.segment.schedule

        super().save(*args, **kwargs)

    def clean(self):
        for field in self.__dict__:
            value = getattr(self, field)
            self.validate_value(value, field)

    def validate_value(self, value, field):
        _validator_func = '_validate_%s' % field

        try:
            validator = getattr(self, _validator_func)
            validator(value)
        except AttributeError:
            pass

    def _validate_status(self, value):
        # status :accpeted by consultant can't change again
        if self.pk:
            old = self.__class__.objects.get(id=self.pk)
            has_accepted = self._has_accepted()

            if old.status == ACCEPT:
                raise ValidationError(
                    {'status': _("Status Accept can't change again")})

            if has_accepted:
                raise ValidationError(
                    {'status': _("Assign has accpeted by %s" % self.consultant.username)})

    def _has_accepted(self):
        # check issue assign has accepted
        queryset = self.__class__.objects \
            .prefetch_related(Prefetch('user'), Prefetch('issue'), Prefetch('consultant')) \
            .select_related('user', 'issue', 'consultant') \
            .filter(status=ACCEPT, issue_id=self.issue.id)
        return queryset.exists()


class AbstractAssigned(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    # who assigned (related as consultant)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='assigneds', editable=False)
    issue = models.ForeignKey('helpdesk.Issue', on_delete=models.CASCADE,
                              related_name='assigneds', editable=False)
    assign = models.ForeignKey('helpdesk.Assign', on_delete=models.CASCADE,
                               related_name='assigneds')

    duedate = models.DateField(null=True, blank=True)
    duetime = models.TimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)

    # related to issue status
    status = models.CharField(choices=ISSUE_STATUS, default=OPEN, max_length=25,
                              validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Assigned")
        verbose_name_plural = _("Assigneds")

    def __str__(self):
        return self.issue.number

    def save(self, *args, **kwargs):
        self.user = self.assign.consultant
        self.issue = self.assign.issue

        if not self.pk:
            slatime = timezone.datetime.strptime(
                str(self.assign.segment.open_hour), '%H:%M:%S')
            duetime = timezone.timedelta(
                hours=self.assign.sla.grace_periode) + slatime
            duetime_fmt = '{0}:{1}:{2}'.format(
                duetime.hour, duetime.minute, duetime.second)

            self.duedate = self.assign.schedule.open_date
            self.duetime = duetime_fmt

        super().save(*args, **kwargs)


class AbstractRespond(models.Model):
    _limit_content_type = models.Q(
        app_label='helpdesk') & models.Q(model__in=['issue'])

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_content_type,
                                     related_name='responds')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Respond")
        verbose_name_plural = _("Responds")


class AbstractRespondLog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='respond_logs')
    respond = models.ForeignKey('helpdesk.Respond', on_delete=models.CASCADE,
                                related_name='respond_logs')

    event = models.CharField(choices=EVENT_CHOICES, max_length=25,
                             validators=[IDENTIFIER_VALIDATOR, non_python_keyword])
    label = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Respond Log")
        verbose_name_plural = _("Respond Logs")

    def __str__(self):
        return self.get_event_display()


class AbstractEntry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='entries')
    respond = models.ForeignKey('helpdesk.Respond', on_delete=models.CASCADE,
                                related_name='entries')
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               related_name='entries')

    subject = models.CharField(max_length=255)
    body = models.TextField()
    classify = models.CharField(choices=CLASSIFY_CHOICES, max_length=25,
                                validators=[IDENTIFIER_VALIDATOR, non_python_keyword])

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Entry")
        verbose_name_plural = _("Entries")

    def __str__(self):
        return self.subject
