from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .schedule.views import ScheduleApiView
from .rrule.views import RuleApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('schedules', ScheduleApiView, basename='schedule')
router.register('rules', RuleApiView, basename='rule')

app_name = 'consultant'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
