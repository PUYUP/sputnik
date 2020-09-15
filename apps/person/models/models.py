from .base import *
from .account import *
from .role import *
from .otp import *
from .experience import *
from .education import *
from .certificate import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
if not is_model_registered('person', 'User'):
    class User(User):
        class Meta(User.Meta):
            db_table = 'person_user'

    __all__.append('User')


# 0
if not is_model_registered('person', 'Profile'):
    class Profile(AbstractProfile):
        class Meta(AbstractProfile.Meta):
            db_table = 'person_profile'

    __all__.append('Profile')


# 1
if not is_model_registered('person', 'Account'):
    class Account(AbstractAccount):
        class Meta(AbstractAccount.Meta):
            db_table = 'person_account'

    __all__.append('Account')


# 2
if not is_model_registered('person', 'Role'):
    class Role(AbstractRole):
        class Meta(AbstractRole.Meta):
            db_table = 'person_role'

    __all__.append('Role')


# 3
if not is_model_registered('person', 'RoleCapabilities'):
    class RoleCapabilities(AbstractRoleCapabilities):
        class Meta(AbstractRoleCapabilities.Meta):
            db_table = 'person_role_capabilities'

    __all__.append('RoleCapabilities')


# 4
if not is_model_registered('person', 'OTPFactory'):
    class OTPFactory(AbstractOTPFactory):
        class Meta(AbstractOTPFactory.Meta):
            db_table = 'person_otp_factory'

    __all__.append('OTPFactory')


# 5
if not is_model_registered('person', 'Experience'):
    class Experience(AbstractExperience):
        class Meta(AbstractExperience.Meta):
            db_table = 'person_experience'

    __all__.append('Experience')


# 6
if not is_model_registered('person', 'ExperienceAttachment'):
    class ExperienceAttachment(AbstractExperienceAttachment):
        class Meta(AbstractExperienceAttachment.Meta):
            db_table = 'person_experience_attachment'

    __all__.append('ExperienceAttachment')


# 7
if not is_model_registered('person', 'Education'):
    class Education(AbstractEducation):
        class Meta(AbstractEducation.Meta):
            db_table = 'person_education'

    __all__.append('Education')


# 8
if not is_model_registered('person', 'EducationAttachment'):
    class EducationAttachment(AbstractEducationAttachment):
        class Meta(AbstractEducationAttachment.Meta):
            db_table = 'person_education_attachment'

    __all__.append('EducationAttachment')


# 9
if not is_model_registered('person', 'Certificate'):
    class Certificate(AbstractCertificate):
        class Meta(AbstractCertificate.Meta):
            db_table = 'person_certificate'

    __all__.append('Certificate')


# 10
if not is_model_registered('person', 'CertificateAttachment'):
    class CertificateAttachment(AbstractCertificateAttachment):
        class Meta(AbstractCertificateAttachment.Meta):
            db_table = 'person_certificate_attachment'

    __all__.append('CertificateAttachment')
