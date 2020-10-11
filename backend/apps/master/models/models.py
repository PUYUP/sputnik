from .scope import *
from .topic import *

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
if not is_model_registered('resume', 'Topic'):
    class Topic(AbstractTopic):
        class Meta(AbstractTopic.Meta):
            db_table = 'master_topic'

    __all__.append('Topic')
