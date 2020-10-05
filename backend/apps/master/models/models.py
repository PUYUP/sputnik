from .scope import *

# PROJECT UTILS
from utils.generals import is_model_registered

__all__ = list()


# 1
if not is_model_registered('resume', 'Scope'):
    class Scope(AbstractScope):
        class Meta(AbstractScope.Meta):
            db_table = 'master_scope'

    __all__.append('Scope')


# 2
if not is_model_registered('resume', 'Skill'):
    class Skill(AbstractSkill):
        class Meta(AbstractSkill.Meta):
            db_table = 'master_skill'

    __all__.append('Skill')
