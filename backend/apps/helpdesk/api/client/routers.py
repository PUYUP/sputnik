from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .v1.issue.views import IssueAPIView
from .v1.consultation.views import ReservationApiView, ReservationItemAPIView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('issues', IssueAPIView, basename='issue')
router.register('reservations', ReservationApiView, basename='reservation')
router.register('reservationsitem', ReservationItemAPIView, basename='reservation_item')

app_name = 'client'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
