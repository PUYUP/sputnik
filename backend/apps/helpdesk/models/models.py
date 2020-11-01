from utils.generals import is_model_registered

from .schedule import *
from .issue import *
from .rule import *
from .attachment import *

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
if not is_model_registered('helpdesk', 'ScheduleTerm'):
    class ScheduleTerm(AbstractScheduleTerm):
        class Meta(AbstractScheduleTerm.Meta):
            db_table = 'helpdesk_schedule_term'

    __all__.append('ScheduleTerm')


# 4
if not is_model_registered('helpdesk', 'Rule'):
    class Rule(AbstractRule):
        class Meta(AbstractRule.Meta):
            db_table = 'helpdesk_schedule_term_rule'

    __all__.append('Rule')


# 5
if not is_model_registered('helpdesk', 'RuleValue'):
    class RuleValue(AbstractRuleValue):
        class Meta(AbstractRuleValue.Meta):
            db_table = 'helpdesk_schedule_term_rule_value'

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
if not is_model_registered('helpdesk', 'Reply'):
    class Reply(AbstractReply):
        class Meta(AbstractReply.Meta):
            db_table = 'helpdesk_reply'

    __all__.append('Reply')


# 12
if not is_model_registered('helpdesk', 'Replied'):
    class Replied(AbstractReplied):
        class Meta(AbstractReplied.Meta):
            db_table = 'helpdesk_replied'

    __all__.append('Replied')


# 13
if not is_model_registered('helpdesk', 'Consultation'):
    class Consultation(AbstractConsultation):
        class Meta(AbstractConsultation.Meta):
            db_table = 'helpdesk_consultation'

    __all__.append('Consultation')


# 14
if not is_model_registered('helpdesk', 'ConsultationLog'):
    class ConsultationLog(AbstractConsultationLog):
        class Meta(AbstractConsultationLog.Meta):
            db_table = 'helpdesk_consultation_log'

    __all__.append('ConsultationLog')


# 15
if not is_model_registered('helpdesk', 'Reservation'):
    class Reservation(AbstractReservation):
        class Meta(AbstractReservation.Meta):
            db_table = 'helpdesk_reservation'

    __all__.append('Reservation')


# 16
if not is_model_registered('helpdesk', 'Entry'):
    class Entry(AbstractEntry):
        class Meta(AbstractEntry.Meta):
            db_table = 'helpdesk_entry'

    __all__.append('Entry')


# 17
if not is_model_registered('helpdesk', 'Assign'):
    class Assign(AbstractAssign):
        class Meta(AbstractAssign.Meta):
            db_table = 'helpdesk_assign'

    __all__.append('Assign')


# 18
if not is_model_registered('helpdesk', 'Assigned'):
    class Assigned(AbstractAssigned):
        class Meta(AbstractAssigned.Meta):
            db_table = 'helpdesk_assigned'

    __all__.append('Assigned')


# 19
if not is_model_registered('helpdesk', 'Gift'):
    class Gift(AbstractGift):
        class Meta(AbstractGift.Meta):
            db_table = 'helpdesk_gift'

    __all__.append('Gift')


# 20
if not is_model_registered('helpdesk', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'helpdesk_attachment'

    __all__.append('Attachment')
