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

OPEN = 'open'
CLOSED = 'closed'
HOLD = 'hold'
RESOLVED = 'resolved'
DELETED = 'deleted'
DRAFT = 'draft'
CONSULT_STATUS = (
    (OPEN, _("Open")),
    (CLOSED, _("Closed")),
    (HOLD, _("Hold")),
    (RESOLVED, _("Resolved")),
    (DELETED, _("Deleted")),
    (DRAFT, _("Draft")),
)

CONSULT = 'consult'
REPLY = 'reply'
CLASSIFY_CHOICES = (
    (CONSULT, _("Consult")),
    (REPLY, _("Reply")),
)

ACCEPT = 'accept'
REJECT = 'reject'
WAITING = 'waiting'
CANCEL = 'cancel'
ASSIGN_STATUS = (
    (ACCEPT, _("Accept")),
    (REJECT, _("Reject")),
    (WAITING, _("Waiting")),
    (CANCEL, _("Cancel")),
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


FREQ_CHOICES = (
    (rrule.YEARLY, _(u"Yearly")),
    (rrule.MONTHLY, _(u"Monthly")),
    (rrule.WEEKLY, _(u"Weekly")),
    (rrule.DAILY, _(u"Daily")),
    (rrule.HOURLY, _(u"Hourly")),
    (rrule.MINUTELY, _(u"Minutely")),
    (rrule.SECONDLY, _(u"Secondly")),
)


WKST_CHOICES = (
    (str(rrule.MO), _(u"Monday")),
    (str(rrule.TU), _(u"Tuesday")),
    (str(rrule.WE), _(u"Wednesday")),
    (str(rrule.TH), _(u"Thursday")),
    (str(rrule.FR), _(u"Friday")),
    (str(rrule.SA), _(u"Saturday")),
    (str(rrule.SU), _(u"Sunday")),
)


(JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC) = range(1, 13)
MONTH_CHOICES = (
    (JAN, _(u"January")),
    (FEB, _(u"February")),
    (MAR, _(u"March")),
    (APR, _(u"April")),
    (MAY, _(u"May")),
    (JUN, _(u"June")),
    (JUL, _(u"July")),
    (AUG, _(u"August")),
    (SEP, _(u"September")),
    (OCT, _(u"October")),
    (NOV, _(u"November")),
    (DEC, _(u"December")),
)


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

EXCLUDE_BYWEEKDAY = 'exclude_byweekday'
EXCLUDE_BYMONTH = 'exclude_bymonth'
EXCLUDE_BYSETPOS = 'exclude_bysetpos'
EXCLUDE_BYMONTHDAY = 'exclude_bymonthday'
EXCLUDE_BYYEARDAY = 'exclude_byyearday'
EXCLUDE_BYWEEKNO = 'exclude_byweekno'
EXCLUDE_BYHOUR = 'exclude_byhour'
EXCLUDE_BYMINUTE = 'exclude_byminute'

LATE_PAYMENT = 'late_payment'
LATE_BOOKING = 'late_booking'
ASSINGN_EXTRA_COST = 'extra_cost'

ATTRIBUTE_CHOICES = (
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

    (EXCLUDE_BYWEEKDAY, _("Exclude Byweekday")),
    (EXCLUDE_BYMONTH, _("Exclude Bymonth")),
    (EXCLUDE_BYSETPOS, _("Exclude Bysetpos")),
    (EXCLUDE_BYMONTHDAY, _("Exclude Bymonthday")),
    (EXCLUDE_BYYEARDAY, _("Exclude Byyearday")),
    (EXCLUDE_BYWEEKNO, _("Exclude Byweekno")),
    (EXCLUDE_BYHOUR, _("Exclude Byhour")),
    (EXCLUDE_BYMINUTE, _("Exclude Byminute")),

    (LATE_PAYMENT, _("Late Payment")),
    (LATE_BOOKING, _("Late Booking")),
    (ASSINGN_EXTRA_COST, ("Extra Cost")),
)


# Attribute types
VARCHAR = "varchar"
INTEGER = "integer"
BOOLEAN = "boolean"
DATE = "date"
DATETIME = "datetime"
ATTRIBUTE_TYPE_CHOICES = (
    (VARCHAR, _("Text")),
    (INTEGER, _("Integer")),
    (BOOLEAN, _("True / False")),
    (DATE, _("Date")),
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
