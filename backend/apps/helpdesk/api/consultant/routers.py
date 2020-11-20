from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .v1.schedule.views import ScheduleApiView, ScheduleExpertiseApiView, ScheduleTermApiView
from .v1.rule.views import RuleApiView, RuleValueApiView
from .v1.segment.views import SegmentApiView
from .v1.sla.views import SLAApiView
from .v1.priority.views import PriorityApiView
from .v1.consultation.views import ReservationApiView
from .v1.assign.views import AssignApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('schedules', ScheduleApiView, basename='schedule')
router.register('schedulesterm', ScheduleTermApiView, basename='scheduleterm')
router.register('expertises', ScheduleExpertiseApiView, basename='expertise')
router.register('rules', RuleApiView, basename='rule')
router.register('rulesvalue', RuleValueApiView, basename='rulevalue')
router.register('segments', SegmentApiView, basename='segment')
router.register('slas', SLAApiView, basename='sla')
router.register('priorities', PriorityApiView, basename='priority')
router.register('reservations', ReservationApiView, basename='reservation')
router.register('assigns', AssignApiView, basename='assign')

app_name = 'consultant'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
