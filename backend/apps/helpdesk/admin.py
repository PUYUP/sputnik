from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from utils.generals import get_model

User = get_model('person', 'User')
Schedule = get_model('helpdesk', 'Schedule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')
Recurrence = get_model('helpdesk', 'Recurrence')
Rule = get_model('helpdesk', 'Rule')
RuleValue = get_model('helpdesk', 'RuleValue')
Segment = get_model('helpdesk', 'Segment')
SLA = get_model('helpdesk', 'SLA')
Priority = get_model('helpdesk', 'Priority')
Issue = get_model('helpdesk', 'Issue')
Respond = get_model('helpdesk', 'Respond')
RespondLog = get_model('helpdesk', 'RespondLog')
Entry = get_model('helpdesk', 'Entry')
Assign = get_model('helpdesk', 'Assign')
Assigned = get_model('helpdesk', 'Assigned')
Gift = get_model('helpdesk', 'Gift')


# Extend Schedule
class SegmentInline(admin.StackedInline):
    model = Segment


class ScheduleExpertiseInline(admin.StackedInline):
    model = ScheduleExpertise


class RecurrenceInline(admin.StackedInline):
    model = Recurrence


class ScheduleExtend(admin.ModelAdmin):
    model = Schedule
    inlines = [RecurrenceInline, ScheduleExpertiseInline, SegmentInline,]


# Extend SLA
class SLAInline(admin.StackedInline):
    model = SLA


class SegmentExtend(admin.ModelAdmin):
    model = Segment
    inlines = [SLAInline,]


# Extend Recurrence
class RuleInline(admin.StackedInline):
    model = Rule


class RecurrenceExtend(admin.ModelAdmin):
    model = Recurrence
    inlines = [RuleInline,]


# Extend Rule
class RuleValueInline(admin.StackedInline):
    model = RuleValue


class RuleExtend(admin.ModelAdmin):
    model = Rule
    inlines = [RuleValueInline,]


admin.site.register(ContentType)
admin.site.register(Schedule, ScheduleExtend)
admin.site.register(Recurrence, RecurrenceExtend)
admin.site.register(Rule, RuleExtend)
admin.site.register(Segment, SegmentExtend)
admin.site.register(SLA)
admin.site.register(Priority)
admin.site.register(Issue)
admin.site.register(Respond)
admin.site.register(RespondLog)
admin.site.register(Entry)
admin.site.register(Assign)
admin.site.register(Assigned)
admin.site.register(Gift)
