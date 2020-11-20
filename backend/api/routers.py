from django.conf import settings
from django.urls import path, include

from rest_framework.schemas import get_schema_view

from apps.person.api import routers as person_routers
from apps.resume.api import routers as resume_routers
from apps.master.api import routers as master_routers
from apps.helpdesk.api import routers as helpdesk_routers

from api.views import RootApiView

_API_VERSION = settings.API_VERSION_SLUG

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path(_API_VERSION + '/master/', include((master_routers, 'master_api'), namespace='master_apis_' + _API_VERSION)),
    path(_API_VERSION + '/person/', include((person_routers, 'person_api'), namespace='person_apis_' + _API_VERSION)),
    path(_API_VERSION + '/helpdesk/', include((helpdesk_routers, 'helpdesk_api'), namespace='helpdesk_apis_' + _API_VERSION)),
    path(_API_VERSION + '/resume/', include((resume_routers, 'resume_api'), namespace='resume_apis_' + _API_VERSION)),

    path('openapi', get_schema_view(
        title="Your Project",
        description="API for all things …",
        version="1.0.0"
    ), name='openapi-schema'),
]
