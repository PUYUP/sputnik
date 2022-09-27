from .attachment import *
from .experience import *
from .education import *
from .certificate import *
from .expertise import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('resume', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'resume_attachment'

    __all__.append('Attachment')


# 2
if not is_model_registered('resume', 'Certificate'):
    class Certificate(AbstractCertificate):
        class Meta(AbstractCertificate.Meta):
            db_table = 'resume_certificate'

    __all__.append('Certificate')


# 3
if not is_model_registered('resume', 'Experience'):
    class Experience(AbstractExperience):
        class Meta(AbstractExperience.Meta):
            db_table = 'resume_experience'

    __all__.append('Experience')


# 4
if not is_model_registered('resume', 'Education'):
    class Education(AbstractEducation):
        class Meta(AbstractEducation.Meta):
            db_table = 'resume_education'

    __all__.append('Education')


# 5
if not is_model_registered('resume', 'Expertise'):
    class Expertise(AbstractExpertise):
        class Meta(AbstractExpertise.Meta):
            db_table = 'resume_expertise'

    __all__.append('Expertise')
