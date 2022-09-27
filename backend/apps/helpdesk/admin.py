from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from utils.generals import get_model

Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')
ScheduleTerm = get_model('helpdesk', 'ScheduleTerm')
Rule = get_model('helpdesk', 'Rule')
RuleValue = get_model('helpdesk', 'RuleValue')
Segment = get_model('helpdesk', 'Segment')
SLA = get_model('helpdesk', 'SLA')
Priority = get_model('helpdesk', 'Priority')
Issue = get_model('helpdesk', 'Issue')
Respond = get_model('helpdesk', 'Respond')
Reply = get_model('helpdesk', 'Reply')
Replied = get_model('helpdesk', 'Replied')
Consultation = get_model('helpdesk', 'Consultation')
ConsultationLog = get_model('helpdesk', 'ConsultationLog')
Entry = get_model('helpdesk', 'Entry')
Assign = get_model('helpdesk', 'Assign')
Assigned = get_model('helpdesk', 'Assigned')
Gift = get_model('helpdesk', 'Gift')
Reservation = get_model('helpdesk', 'Reservation')
ReservationRule = get_model('helpdesk', 'ReservationRule')
ReservationItem = get_model('helpdesk', 'ReservationItem')
Attachment = get_model('helpdesk', 'Attachment')
Invoice = get_model('helpdesk', 'Invoice')
InvoiceItem = get_model('helpdesk', 'InvoiceItem')


# Extend Schedule
class SegmentInline(admin.StackedInline):
    model = Segment


class ScheduleExpertiseInline(admin.StackedInline):
    model = ScheduleExpertise


class ScheduleTermInline(admin.StackedInline):
    model = ScheduleTerm


class ScheduleExtend(admin.ModelAdmin):
    model = Schedule
    inlines = [ScheduleTermInline, ScheduleExpertiseInline, SegmentInline,]


# Extend SLA
class SLAInline(admin.StackedInline):
    model = SLA


class SegmentExtend(admin.ModelAdmin):
    model = Segment
    inlines = [SLAInline,]


# Extend ScheduleTerm
class RuleInline(admin.StackedInline):
    model = Rule


class ScheduleTermExtend(admin.ModelAdmin):
    model = ScheduleTerm
    inlines = [RuleInline,]


# Extend Rule
class RuleValueInline(admin.StackedInline):
    model = RuleValue


class RuleExtend(admin.ModelAdmin):
    model = Rule
    inlines = [RuleValueInline,]


admin.site.register(ContentType)
admin.site.register(Schedule, ScheduleExtend)
admin.site.register(ScheduleTerm, ScheduleTermExtend)
admin.site.register(Rule, RuleExtend)
admin.site.register(RuleValue)
admin.site.register(Segment, SegmentExtend)
admin.site.register(SLA)
admin.site.register(Priority)
admin.site.register(Issue)
admin.site.register(Respond)
admin.site.register(Reply)
admin.site.register(Replied)
admin.site.register(Consultation)
admin.site.register(ConsultationLog)
admin.site.register(Entry)
admin.site.register(Assign)
admin.site.register(Assigned)
admin.site.register(Gift)
admin.site.register(Reservation)
admin.site.register(ReservationRule)
admin.site.register(ReservationItem)
admin.site.register(Attachment)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
