from utils.generals import is_model_registered

from .schedule import *
from .issue import *
from .rrule import *

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
if not is_model_registered('helpdesk', 'Recurrence'):
    class Recurrence(AbstractRecurrence):
        class Meta(AbstractRecurrence.Meta):
            db_table = 'helpdesk_recurrence'

    __all__.append('Recurrence')


# 4
if not is_model_registered('helpdesk', 'Rule'):
    class Rule(AbstractRule):
        class Meta(AbstractRule.Meta):
            db_table = 'helpdesk_recurrence_rule'

    __all__.append('Rule')


# 5
if not is_model_registered('helpdesk', 'RuleValue'):
    class RuleValue(AbstractRuleValue):
        class Meta(AbstractRuleValue.Meta):
            db_table = 'helpdesk_recurrence_rule_value'

    __all__.append('RuleValue')


# 6
if not is_model_registered('helpdesk', 'Segment'):
    class Segment(AbstractSegment):
        class Meta(AbstractSegment.Meta):
            db_table = 'helpdesk_segment'

    __all__.append('Segment')


# 7
if not is_model_registered('helpdesk', 'SLA'):
    class SLA(AbstractSLA):
        class Meta(AbstractSLA.Meta):
            db_table = 'helpdesk_sla'

    __all__.append('SLA')


# 8
if not is_model_registered('helpdesk', 'Priority'):
    class Priority(AbstractPriority):
        class Meta(AbstractPriority.Meta):
            db_table = 'helpdesk_priority'

    __all__.append('Priority')


# 9
if not is_model_registered('helpdesk', 'Issue'):
    class Issue(AbstractIssue):
        class Meta(AbstractIssue.Meta):
            db_table = 'helpdesk_issue'

    __all__.append('Issue')


# 10
if not is_model_registered('helpdesk', 'Respond'):
    class Respond(AbstractRespond):
        class Meta(AbstractRespond.Meta):
            db_table = 'helpdesk_respond'

    __all__.append('Respond')


# 11
if not is_model_registered('helpdesk', 'RespondLog'):
    class RespondLog(AbstractRespondLog):
        class Meta(AbstractRespondLog.Meta):
            db_table = 'helpdesk_respond_log'

    __all__.append('RespondLog')


# 12
if not is_model_registered('helpdesk', 'Entry'):
    class Entry(AbstractEntry):
        class Meta(AbstractEntry.Meta):
            db_table = 'helpdesk_entry'

    __all__.append('Entry')


# 13
if not is_model_registered('helpdesk', 'Assign'):
    class Assign(AbstractAssign):
        class Meta(AbstractAssign.Meta):
            db_table = 'helpdesk_assign'

    __all__.append('Assign')


# 14
if not is_model_registered('helpdesk', 'Assigned'):
    class Assigned(AbstractAssigned):
        class Meta(AbstractAssigned.Meta):
            db_table = 'helpdesk_assigned'

    __all__.append('Assigned')


# 15
if not is_model_registered('helpdesk', 'Gift'):
    class Gift(AbstractGift):
        class Meta(AbstractGift.Meta):
            db_table = 'helpdesk_gift'

    __all__.append('Gift')
