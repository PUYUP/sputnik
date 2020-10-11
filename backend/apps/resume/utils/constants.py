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
EXPERTISE_LEVELS = (
    (BEGINNER, _(u"Beginner")),
    (AVERAGE, _(u"Average")),
    (SKILLED, _(u"Skilled")),
    (SPECIALIST, _(u"Specialist")),
    (EXPERT, _(u"Expert")),
)


PUBLISH = 'publish'
DRAFT = 'draft'
EDUCATION_STATUS = (
    (PUBLISH, _("Publish")),
    (DRAFT, _("Draft")),
)
EXPERIENCE_STATUS = EDUCATION_STATUS
CERTIFICATE_STATUS = EDUCATION_STATUS
