from django.urls import path, include

from rest_framework.routers import DefaultRouter

# Base
from apps.helpdesk.api.base.views import TopicApiView

# Expert
from apps.helpdesk.api.expert.expert.views import ExpertApiView
from apps.helpdesk.api.expert.expertise.views import ExpertiseApiView
from apps.helpdesk.api.expert.schedule.views import ScheduleApiView

# Create a router and register our viewsets with it.
# Base router
router_base = DefaultRouter()
router_base.register('topics', TopicApiView, basename='topic')

# Expert router
router_expert = DefaultRouter()
router_expert.register('experts', ExpertApiView, basename='expert')
router_expert.register('expertises', ExpertiseApiView, basename='expertise')
router_expert.register('schedules', ScheduleApiView, basename='schedule')

app_name = 'helpdesk'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('base/', include(router_base.urls)),
    path('expert/', include(router_expert.urls)),
]
