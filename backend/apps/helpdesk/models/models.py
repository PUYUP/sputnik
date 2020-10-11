from utils.generals import is_model_registered

from .eav import *
from .schedule import *
from .issue import *

__all__ = []


# 1
if not is_model_registered('helpdesk', 'Schedule'):
    class Schedule(AbstractSchedule):
        class Meta(AbstractSchedule.Meta):
            db_table = 'helpdesk_schedule'

    __all__.append('Schedule')


# 2
if not is_model_registered('helpdesk', 'ScheduleExpertise'):
    class ScheduleExpertise(AbstractScheduleExpertise):
        class Meta(AbstractScheduleExpertise.Meta):
            db_table = 'helpdesk_schedule_expertise'

    __all__.append('ScheduleExpertise')


# 3
if not is_model_registered('helpdesk', 'Attribute'):
    class Attribute(AbstractAttribute):
        class Meta(AbstractAttribute.Meta):
            db_table = 'helpdesk_attribute'

    __all__.append('Attribute')


# 4
if not is_model_registered('helpdesk', 'AttributeValue'):
    class AttributeValue(AbstractAttributeValue):
        class Meta(AbstractAttributeValue.Meta):
            db_table = 'helpdesk_attribute_value'

    __all__.append('AttributeValue')


# 5
if not is_model_registered('helpdesk', 'Segment'):
    class Segment(AbstractSegment):
        class Meta(AbstractSegment.Meta):
            db_table = 'helpdesk_segment'

    __all__.append('Segment')


# 6
if not is_model_registered('helpdesk', 'SLA'):
    class SLA(AbstractSLA):
        class Meta(AbstractSLA.Meta):
            db_table = 'helpdesk_sla'

    __all__.append('SLA')


# 7
if not is_model_registered('helpdesk', 'Priority'):
    class Priority(AbstractPriority):
        class Meta(AbstractPriority.Meta):
            db_table = 'helpdesk_priority'

    __all__.append('Priority')


# 8
if not is_model_registered('helpdesk', 'Issue'):
    class Issue(AbstractIssue):
        class Meta(AbstractIssue.Meta):
            db_table = 'helpdesk_issue'

    __all__.append('Issue')


# 9
if not is_model_registered('helpdesk', 'Respond'):
    class Respond(AbstractRespond):
        class Meta(AbstractRespond.Meta):
            db_table = 'helpdesk_respond'

    __all__.append('Respond')


# 10
if not is_model_registered('helpdesk', 'RespondLog'):
    class RespondLog(AbstractRespondLog):
        class Meta(AbstractRespondLog.Meta):
            db_table = 'helpdesk_respond_log'

    __all__.append('RespondLog')


# 11
if not is_model_registered('helpdesk', 'Entry'):
    class Entry(AbstractEntry):
        class Meta(AbstractEntry.Meta):
            db_table = 'helpdesk_entry'

    __all__.append('Entry')


# 12
if not is_model_registered('helpdesk', 'Assign'):
    class Assign(AbstractAssign):
        class Meta(AbstractAssign.Meta):
            db_table = 'helpdesk_assign'

    __all__.append('Assign')


# 13
if not is_model_registered('helpdesk', 'Assigned'):
    class Assigned(AbstractAssigned):
        class Meta(AbstractAssigned.Meta):
            db_table = 'helpdesk_assigned'

    __all__.append('Assigned')


# 14
if not is_model_registered('helpdesk', 'Gift'):
    class Gift(AbstractGift):
        class Meta(AbstractGift.Meta):
            db_table = 'helpdesk_gift'

    __all__.append('Gift')
