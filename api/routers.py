from django.urls import path, include

from api.views import RootApiView

from apps.person.api import routers as person_routers
from apps.helpdesk.api import routers as helpdesk_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('v1/person/', include((person_routers, 'person'), namespace='persons')),
    path('v1/helpdesk/', include((helpdesk_routers, 'helpdesk'), namespace='helpdesks')),
]
