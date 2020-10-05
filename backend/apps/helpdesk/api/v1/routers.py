from django.urls import path, include

from rest_framework.routers import DefaultRouter

# Consultant
from .consultant.schedule.views import ScheduleApiView

# Create a router and register our viewsets with it.
# Consultant router
router_consultant = DefaultRouter()
router_consultant.register('schedules', ScheduleApiView, basename='schedule')

app_name = 'helpdesk'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('consultant/', include(router_consultant.urls)),
]
