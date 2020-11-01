from django.utils.translation import ugettext_lazy as _


REGISTERED = 'registered'
CLIENT = 'client'
CONSULTANT = 'consultant'
ROLE_IDENTIFIERS = (
    (REGISTERED, _(u"Registered")),
    (CLIENT, _(u"Client")),
    (CONSULTANT, _(u"Consultant")),
)

ROLE_DEFAULTS = (
    (REGISTERED, _(u"Registered")),
)

ROLE_ALLOWED = (
    (CLIENT, _(u"Client")),
    (CONSULTANT, _(u"Consultant")),
)


VerifyCode_SESSION_FIELDS = ['uuid', 'token', 'challenge', 'msisdn', 'email', 'info']
EMAIL_VALIDATION = 'email_validation'
MSISDN_VALIDATION = 'msisdn_validation'
REGISTER_VALIDATION = 'register_validation'
PASSWORD_RECOVERY = 'password_recovery'
CHANGE_MSISDN = 'change_msisdn'
CHANGE_EMAIL = 'change_email'
CHANGE_USERNAME = 'change_username'
CHANGE_PASSWORD = 'change_password'
VerifyCode_CHALLENGE = (
    (EMAIL_VALIDATION, _(u"Email Validation")),
    (MSISDN_VALIDATION, _(u"MSISDN Validation")),
    (REGISTER_VALIDATION, _(u"Register Validation")),
    (PASSWORD_RECOVERY, _(u"Password Recovery")),
    (CHANGE_MSISDN, _(u"Change MSISDN")),
    (CHANGE_EMAIL, _(u"Change Email")),
    (CHANGE_USERNAME, _(u"Change Username")),
    (CHANGE_PASSWORD, _(u"Change Password")),
)


UNDEFINED = 'unknown'
MALE = 'male'
FEMALE = 'female'
GENDER_CHOICES = (
    (UNDEFINED, _(u"Unknown")),
    (MALE, _(u"Male")),
    (FEMALE, _(u"Female")),
)


PUBLISH = 'publish'
DRAFT = 'draft'
EDUCATION_STATUS = (
    (PUBLISH, _("Publish")),
    (DRAFT, _("Draft")),
)
EXPERIENCE_STATUS = EDUCATION_STATUS
CERTIFICATE_STATUS = EDUCATION_STATUS
