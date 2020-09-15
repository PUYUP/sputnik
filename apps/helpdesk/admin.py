from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from utils.generals import get_model

Scope = get_model('helpdesk', 'Scope')
Topic = get_model('helpdesk', 'Topic')
Expertise = get_model('helpdesk', 'Expertise')
Schedule = get_model('helpdesk', 'Schedule')
Attribute = get_model('helpdesk', 'Attribute')
AttributeValue = get_model('helpdesk', 'AttributeValue')
Segment = get_model('helpdesk', 'Segment')
SLA = get_model('helpdesk', 'SLA')
Priority = get_model('helpdesk', 'Priority')
Consult = get_model('helpdesk', 'Consult')
Respond = get_model('helpdesk', 'Respond')
RespondLog = get_model('helpdesk', 'RespondLog')
Entry = get_model('helpdesk', 'Entry')
Assign = get_model('helpdesk', 'Assign')
Assigned = get_model('helpdesk', 'Assigned')
Gift = get_model('helpdesk', 'Gift')


# Extend Schedule
class SegmentInline(admin.StackedInline):
    model = Segment


class ScheduleExtend(admin.ModelAdmin):
    model = Schedule
    inlines = [SegmentInline,]


# Extend Schedule Attribute
class AttributeValueInline(admin.StackedInline):
    model = AttributeValue


# Extend SLA
class SLAInline(admin.StackedInline):
    model = SLA


class SegmentExtend(admin.ModelAdmin):
    model = Segment
    inlines = [SLAInline,]


# Extend Expertise
class ExpertiseExtend(admin.ModelAdmin):
    model = Expertise
    list_display = ('topic', 'user',)


# Extend Topic
class TopicInline(admin.StackedInline):
    model = Topic


class ScopeExtend(admin.ModelAdmin):
    model = Scope
    inlines = [TopicInline,]


admin.site.register(ContentType)
admin.site.register(Scope, ScopeExtend)
admin.site.register(Expertise, ExpertiseExtend)
admin.site.register(Schedule, ScheduleExtend)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(Segment, SegmentExtend)
admin.site.register(Topic)
admin.site.register(SLA)
admin.site.register(Priority)
admin.site.register(Consult)
admin.site.register(Respond)
admin.site.register(RespondLog)
admin.site.register(Entry)
admin.site.register(Assign)
admin.site.register(Assigned)
admin.site.register(Gift)
