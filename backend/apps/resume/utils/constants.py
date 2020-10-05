from django.utils.translation import ugettext_lazy as _


FULL_TIME = 'full_time'
PART_TIME = 'part_time'
SELF_EMPLOYED = 'self_employed'
FREELANCE = 'freelance'
CONTRACT = 'contract'
INTERNSHIP = 'internship'
APPRENTICESHIP = 'apprenticeship'

EMPLOYMENT_CHOICES = (
    (FULL_TIME, _(u"Full-time")),
    (PART_TIME, _(u"Part-time")),
    (SELF_EMPLOYED, _(u"Self-employed")),
    (FREELANCE, _(u"Freelance")),
    (CONTRACT, _(u"Contract")),
    (INTERNSHIP, _(u"Internship")),
    (APPRENTICESHIP, _(u"Apprenticeship")),
)


BEGINNER = 'beginner'
AVERAGE = 'average'
SKILLED = 'skilled'
SPECIALIST = 'specialist'
EXPERT = 'expert'
SKILL_LEVELS = (
    (BEGINNER, _(u"Beginner")),
    (AVERAGE, _(u"Average")),
    (SKILLED, _(u"Skilled")),
    (SPECIALIST, _("uSpecialist")),
    (EXPERT, _(u"Expert")),
)


JAN = '1'
FEB = '2'
MAR = '3'
APR = '4'
MAY = '5'
JUN = '6'
JUL = '7'
AUG = '8'
SEP = '9'
OCT = '10'
NOV = '11'
DEC = '12'

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


PUBLISH = 'publish'
DRAFT = 'draft'
EDUCATION_STATUS = (
    (PUBLISH, _("Publish")),
    (DRAFT, _("Draft")),
)
EXPERIENCE_STATUS = EDUCATION_STATUS
CERTIFICATE_STATUS = EDUCATION_STATUS
