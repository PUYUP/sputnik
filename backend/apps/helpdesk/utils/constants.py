from dateutil import rrule
from django.utils.translation import ugettext_lazy as _

TEXT = 'text'
VOICE = 'voice'
VIDEO = 'video'
CANAL_CHOICES = (
    (TEXT, _("Text")),
    (VOICE, _("Voice")),
    (VIDEO, _("Video")),
)

HIGH = 'high'
MEDIUM = 'medium'
LOW = 'low'
PRIORITY_CHOICES = (
    (HIGH, _("High")),
    (MEDIUM, _("Medium")),
    (LOW, _("Low")),
)


OPEN = 'open'
CLOSED = 'closed'
HOLD = 'hold'
RESOLVED = 'resolved'
DELETED = 'deleted'
DRAFT = 'draft'
ISSUE_STATUS = (
    (OPEN, _("Open")),
    (CLOSED, _("Closed")),
    (HOLD, _("Hold")),
    (RESOLVED, _("Resolved")),
    (DELETED, _("Deleted")),
    (DRAFT, _("Draft")),
)

ISSUE = 'issue'
REPLY = 'reply'
CLASSIFY_CHOICES = (
    (ISSUE, _("Issue")),
    (REPLY, _("Reply")),
)

ACCEPT = 'accept'
REJECT = 'reject'
WAITING = 'waiting'
ASSIGN_STATUS = (
    (ACCEPT, _("Accept")),
    (REJECT, _("Reject")),
    (WAITING, _("Waiting")),
)

CREATED = 'created'
ASSIGNED = 'assigned'
TRANSFERRED = 'transferred'
OVERDUE = 'overdue'
VIEWED = 'viewed'
EVENT_CHOICES = (
    (CREATED, _("Created")),
    (ASSIGNED, _("Assigned")),
    (TRANSFERRED, _("Transferred")),
    (OVERDUE, _("Overdue")),
    (VIEWED, _("Viewed")),
    (CLOSED, _("Closed")),
    (DELETED, _("Deleted")),
)


RRULE_FREQ_CHOICES = (
    (rrule.YEARLY, _(u"Yearly")),
    (rrule.MONTHLY, _(u"Monthly")),
    (rrule.WEEKLY, _(u"Weekly")),
    (rrule.DAILY, _(u"Daily")),
    (rrule.HOURLY, _(u"Hourly")),
    (rrule.MINUTELY, _(u"Minutely")),
    (rrule.SECONDLY, _(u"Secondly")),
)


setattr(rrule, 'FD', 'FD')
RRULE_WKST_CHOICES = (
    (str(rrule.MO), _(u"Monday")),
    (str(rrule.TU), _(u"Tuesday")),
    (str(rrule.WE), _(u"Wednesday")),
    (str(rrule.TH), _(u"Thursday")),
    (str(rrule.FR), _(u"Friday")),
    (str(rrule.SA), _(u"Saturday")),
    (str(rrule.SU), _(u"Sunday")),
    (str(rrule.FD), _(u"Few days")),
)


EXCLUSION = 'exclusion'
INCLUSION = 'inclusion'
RRULE_MODE_CHOICES = (
    (INCLUSION, _('Inclusion')),
    (EXCLUSION, _('Exclusion')),
)


BYDATE = 'bydate'
BYWEEKDAY = 'byweekday'
BYMONTH = 'bymonth'
BYSETPOS = 'bysetpos'
BYMONTHDAY = 'bymonthday'
BYYEARDAY = 'byyearday'
BYWEEKNO = 'byweekno'
BYHOUR = 'byhour'
BYMINUTE = 'byminute'
BYSECOND = 'bysecond'
BYEASTER = 'byeaster'

LATE_PAYMENT = 'late_payment'
LATE_BOOKING = 'late_booking'
ASSIGN_EXTRA_COST = 'extra_cost'

RRULE_IDENTIFIER_CHOICES = (
    (BYDATE, _("Bydate")),
    (BYWEEKDAY, _("Byweekday")),
    (BYMONTH, _("Bymonth")),
    (BYSETPOS, _("Bysetpos")),
    (BYMONTHDAY, _("Bymonthday")),
    (BYYEARDAY, _("Byyearday")),
    (BYWEEKNO, _("Byweekno")),
    (BYHOUR, _("Byhour")),
    (BYMINUTE, _("Byminute")),
    (BYSECOND, _("Bysecond")),
    (BYEASTER, _("Byeaster")),
)


RECUR = 'recur'
ONCE = 'once'
RRULE_RECURRENCE_CHOICES = (
    (RECUR, _("Recur")),
    (ONCE, _("Once")),
)


# RRule types
VARCHAR = "varchar"
INTEGER = "integer"
DATETIME = "datetime"
RRULE_TYPE_CHOICES = (
    (VARCHAR, _("Text")),
    (INTEGER, _("Integer")),
    (DATETIME, _("Datetime")),
)


HOUR = 'hour'
DAY = 'day'
MONTH = 'month'
YEAR = 'year'
DEADLINE_UNIT_CHOICES = (
    (HOUR, _("Hour")),
    (DAY, _("Day")),
    (MONTH, _("Month")),
    (YEAR, _("Year")),
)


PUSH = 'push'
PULL = 'pull'
RSV_DATE_STATUS = (
    (PUSH, _("Push")),
    (PULL, _("Pull")),
)


PENDING = 'pending'
PAID = 'paid'
PAYMENT_STATUS = (
    (PENDING, _("Pending")),
    (PAID, _("Paid")),
)
