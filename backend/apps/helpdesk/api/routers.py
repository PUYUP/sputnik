from django.urls import path, include

from .consultant import routers as consultant_routers
from .client import routers as client_routers

app_name = 'helpdesk_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('consultant/', include(consultant_routers)),
    path('client/', include(client_routers)),
]
