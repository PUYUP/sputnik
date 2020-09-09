from .base import *
from .project import *

# check setting load from live server
# this time all live server mark as production grade
if os.environ.get('PRODUCTION', False):
    from .production import *
else:
    from .development import *


# CACHING SERVER
CACHES['default']['LOCATION'] = '10.0.2.2:11211' # or REDIS_URL
