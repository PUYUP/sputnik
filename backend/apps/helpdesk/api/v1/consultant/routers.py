from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .schedule.views import ScheduleApiView, ScheduleExpertiseApiView, RecurrenceApiView
from .rrule.views import RuleApiView
from .segment.views import SegmentApiView
from .sla.views import SLAApiView
from .priority.views import PriorityApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('schedules', ScheduleApiView, basename='schedule')
router.register('expertises', ScheduleExpertiseApiView, basename='expertise')
router.register('recurrences', RecurrenceApiView, basename='recurrence')
router.register('rules', RuleApiView, basename='rule')
router.register('segments', SegmentApiView, basename='segment')
router.register('slas', SLAApiView, basename='sla')
router.register('priorities', PriorityApiView, basename='priority')

app_name = 'consultant'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
