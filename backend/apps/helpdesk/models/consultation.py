import uuid

from django.urls import reverse
from django.conf import settings
from django.db import models
from django.db.models import Q, F, Count, Exists, OuterRef, IntegerField, ExpressionWrapper
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from utils.validators import non_python_keyword, identifier_validator
from utils.generals import random_string, get_model
from apps.helpdesk.utils.constants import (
    ACCEPT, ISSUE_STATUS, OPEN, ASSIGN_STATUS, PULL, PUSH, REJECT, RSV_DATE_STATUS, 
    WAITING, EVENT_CHOICES
)


class ReservationQuerySet(models.query.QuerySet):
    @property
    def assign_query(self):
        Assign = get_model('helpdesk', 'Assign')

        qs = Assign.objects.filter(reservation_item__uuid=OuterRef('reservation_item__uuid'))
        return qs

    def filter_assign(self, assign_status=None, rsv_item_status=None):
        # rsv_item_status: pull, push
        # assign_status: accept, reject, waiting
        # rsv = reservation

        q = Q(status=assign_status) & Q(reservation_item__status=PUSH)

        if rsv_item_status == PULL:
            q = Q(reservation_item__status=rsv_item_status)

        qs_assign = self.assign_query.filter(q)
        qs = self.annotate(assign_exist=Exists(qs_assign),
                           assigned_count=Count('reservation_item__assign__assigned', distinct=True),
                           rsv_item_cost=F('reservation_item__sla__cost') + F('reservation_item__priority__cost'),
                           total_cost=ExpressionWrapper(F('assigned_count') * F('rsv_item_cost'), output_field=IntegerField())) \
            .filter(assign_exist=True)

        return qs


class AbstractIssue(models.Model):
    """ 
    STEP 1:
    CLIENT create many Issue
    CLIENT can ASSIGN (then ASSIGNED) Issue to multiple CONSULTANT
    So CLIENT has a different RESPOND, then can compared them
    But each RESPOND independent, mean CLIENT must pay all
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='issue')
    topic = models.ManyToManyField('master.Topic', related_name='issue',
                                   limit_choices_to={'is_active': True})

    label = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")

    def __str__(self):
        return self.label

    @property
    def permalink(self):
        from django.urls import reverse
        return reverse('helpdesk_view:client:issue_detail', kwargs={'uuid': self.uuid})


class AbstractReservation(models.Model):
    """
    A.k CART
    -------------------------
    STEP 2:
    CLIENT Reservation Issue to CONSULTANT

    -----------------------

    Maybe has multiple day, split to ReservationItem
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_reservation')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='consultant_reservation')

    number = models.CharField(max_length=255, editable=False, unique=True, null=True)
    objects = ReservationQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")

    def __str__(self):
        return self.client.username

    @property
    def permalink_for_client(self):
        return reverse('helpdesk_view:client:reservation_detail', kwargs={'uuid': self.uuid})

    @property
    def permalink_for_consultant(self):
        return reverse('helpdesk_view:consultant:reservation_detail', kwargs={'uuid': self.uuid})


class AbstractReservationItem(models.Model):
    """
    A.k CART ITEM
    -------------------------
    Reservation possible to have multiple date / day
    Each reserved day has standalone Issue, Schedule, Segment, SLA and Priority
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    reservation = models.ForeignKey('helpdesk.Reservation', on_delete=models.CASCADE,
                                    related_name='reservation_item')
    issue = models.ForeignKey('helpdesk.Issue', on_delete=models.CASCADE,
                              related_name='reservation_item')
    schedule = models.ForeignKey('helpdesk.Schedule', on_delete=models.CASCADE,
                                 related_name='reservation_item')
    segment = models.ForeignKey('helpdesk.Segment', on_delete=models.CASCADE,
                                related_name='reservation_item')
    sla = models.ForeignKey('helpdesk.SLA', on_delete=models.CASCADE,
                            related_name='reservation_item')
    priority = models.ForeignKey('helpdesk.Priority', on_delete=models.CASCADE,
                                 related_name='reservation_item')

    datetime = models.DateTimeField(auto_now_add=False)
    number = models.CharField(max_length=255, editable=False, unique=True, null=True)
    status = models.CharField(choices=RSV_DATE_STATUS, default=PUSH, max_length=15)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Reservation Item")
        verbose_name_plural = _("Reservation Items")

    def __str__(self):
        return str(self.datetime)

    @property
    def assign_status(self):
        return self.assign.status

    @property
    def total_cost(self):
        return self.sla.cost + self.priority.cost

    @property
    def issue_label(self):
        issue = self.reservation.issue
        return issue.label

    def save(self, *args, **kwargs):
        if not self.pk:
            rand = random_string(8)
            now = timezone.datetime.now()
            timestamp = timezone.datetime.timestamp(now)
            number = '{}{}'.format(rand, int(timestamp))

            self.number = number
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
        except AttributeError as e:
            pass

    def _validate_status(self, value):
        if self.id:
            if self.assign_status == ACCEPT:
                raise ValidationError({'detail': _("Accepted by Consultant, can't change again")})

            if self.assign_status == REJECT:
                raise ValidationError({'detail': _("Rejected by Consultant, can't change again")})
        
        else:
            # Can't use old date
            x = self.datetime
            y = timezone.now()

            if x < y:
                raise ValidationError({'datetime': _("Can't use old date")})


class AbstractAssign(models.Model):
    """
    A.k PRE-ORDER
    -------------------------
    STEP 3:
    CONSULTANT checking...
    Assign Reservation to CONSULTANT
    at this point CONSULTANT can accept or reject
    - if reject CLIENT can't pay it
    - if accept CLIENT can continue to pay

    Each ReservationItem have standalone Assign
    Because allow multidate select
    Eg: I want Reservation date 23, 30, and 5 in month
    -------------------------

    Hay CONSULTANT can you accept my Issue?
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_assign')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='consultant_assign')
    reservation = models.ForeignKey('helpdesk.Reservation', on_delete=models.CASCADE,
                                    related_name='assign')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Assign")
        verbose_name_plural = _("Assigns")
        constraints = [
            models.UniqueConstraint(
                fields=['client', 'consultant', 'reservation'], 
                name='unique_assign'
            )
        ]

    def __str__(self):
        return self.reservation.number

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
        if self.pk:
            if self.reservation_item.status != PUSH:
                raise ValidationError({'reservation_item': _("Pulled by client")})

            old = self.__class__.objects.get(id=self.pk)
            if old.status != WAITING:
                raise ValidationError({'status': _("Status Accept / Reject can't change again")})


class AbstractAssigned(models.Model):
    """
    A.k ORDER ITEM
    -------------------------
    STEP 4: create by consultant
    At this point indicated the Issued Accepted by CONSULTANT 
    and CLIENT has paid! So Consult can run.

    This will create Invoice to
    
    -------------------------

    Hay CLIENT, I accepted so pay now
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_assigned')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='consultant_assigned')
    assign = models.OneToOneField('helpdesk.Assign', on_delete=models.CASCADE,
                                  related_name='assigned')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Assigned")
        verbose_name_plural = _("Assigneds")
        constraints = [
            models.UniqueConstraint(
                fields=['client', 'consultant', 'assign'], 
                name='unique_assigned'
            )
        ]

    def __str__(self):
        return self.consultant.username


class AbstractReservationRule(models.Model):
    """
    Sometime Reservation related to Rule
    Ex: byweekday, when Client request Reservation they choice day
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    reservation = models.ForeignKey('helpdesk.Reservation', on_delete=models.CASCADE,
                                    related_name='reservation_rule')
    reservation_item = models.ForeignKey('helpdesk.ReservationItem', on_delete=models.CASCADE,
                                         related_name='reservation_rule')
    rule = models.ForeignKey('helpdesk.Rule', on_delete=models.CASCADE,
                             related_name='reservation_rule', editable=False)
    rule_value = models.ForeignKey('helpdesk.RuleValue', on_delete=models.CASCADE,
                                   related_name='reservation_rule')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Reservation Rule")
        verbose_name_plural = _("Reservation Rules")

    def __str__(self):
        return self.reservation.client.username

    def save(self, *args, **kwargs):
        self.rule = self.rule_value.rule
        super().save(*args, **kwargs)


class AbstractConsultation(models.Model):
    """
    STEP 5:
    Issued started consultation with CLIENT and CONSULTANT
    This object created after Assigned action
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='client_consultation')
    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='consultant_consultation')
    assigned = models.ForeignKey('helpdesk.Assigned', on_delete=models.CASCADE,
                                 related_name='consultation')
    issue = models.ForeignKey('helpdesk.Issue', on_delete=models.CASCADE,
                              related_name='consultation', editable=False)

    status = models.CharField(max_length=25, choices=ISSUE_STATUS, default=OPEN,
                              validators=[non_python_keyword, identifier_validator])
    duedate = models.DateField(null=True, blank=True)
    duetime = models.TimeField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Consultation")
        verbose_name_plural = _("Consultations")

    @property
    def issue_label(self):
        return self.assigned.assign.reservation.issue.label

    @property
    def segment(self):
        return self.assigned.assign.reservation.segment

    @property
    def is_overdue(self):
        return False

    def __str__(self) -> str:
        return self.issue_label

    def save(self, *args, **kwargs):
        # auto populate issue value
        self.issue = self.assigned.assign.reservation.issue

        # set due
        if not self.pk:
            slatime = timezone.datetime.strptime(
                str(self.segment.open_hour), '%H:%M:%S')

            duetime = timezone.timedelta(
                hours=self.segment.sla.grace_periode) + slatime

            duetime_fmt = '{0}:{1}:{2}'.format(
                duetime.hour, duetime.minute, duetime.second)

            self.duedate = self.segment.schedule.open_date
            self.duetime = duetime_fmt
        return super().save(*args, **kwargs)


class AbstractConsultationLog(models.Model):
    _limit_ct = models.Q(app_label='helpdesk')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_ct,
                                     related_name='consultation_log')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    column = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField()
    event = models.CharField(choices=EVENT_CHOICES, max_length=25,
                             validators=[non_python_keyword, identifier_validator])

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Consultation Log")
        verbose_name_plural = _("Consultation Logs")

    def __str__(self):
        return self.new_value


class AbstractRespond(models.Model):
    """
    Respond is independent so CONSULTANT can re-used to another Issue
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='respond')
    label = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Respond")
        verbose_name_plural = _("Responds")

    def __str__(self):
        return self.label if self.label else self.description[0:25]


class AbstractReply(models.Model):
    """
    Reply is independent so CONSULTANT can re-used to another Respond
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='reply')
    label = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Reply")
        verbose_name_plural = _("Replies")

    def __str__(self):
        return self.label if self.label else self.description[0:25]


class AbstractReplied(models.Model):
    """
    Mapping Respond and Reply
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='replied')
    respond = models.ForeignKey('helpdesk.Respond', on_delete=models.CASCADE,
                                related_name='replied')
    reply = models.ForeignKey('helpdesk.Reply', on_delete=models.CASCADE,
                              related_name='reply_replied')
    parent = models.ForeignKey('helpdesk.Reply', on_delete=models.CASCADE,
                               related_name='parent_replied', null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Replied")
        verbose_name_plural = _("Replieds")

    def __str__(self):
        return self.reply.label if self.reply.label else self.reply.description[0:25]


class AbstractEntry(models.Model):
    """
    Mapping entries
    The Tree:
    - Consultation
    --- issue (from Issue model)
    --- respond (from Respond model)
    --- reply (from Reply model)
    --- log (from ConsultationLog model)
    """
    _limit_ct = models.Q(app_label='helpdesk') & models.Q(
        model__in=['issue' 'respond', 'replied', 'consultationlog'])

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='entry')
    consultation = models.ForeignKey('helpdesk.Consultation', on_delete=models.CASCADE,
                                     related_name='entry')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     limit_choices_to=_limit_ct,
                                     related_name='entry')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'helpdesk'
        ordering = ['-create_date']
        verbose_name = _("Entry")
        verbose_name_plural = _("Entries")

    def __str__(self):
        return self.subject
