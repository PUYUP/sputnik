from django.urls import path

from .v1.consultation import (
    Client_IssueView, 
    Client_IssueDetailView, 
    Client_ReservationChangeView,
    Client_ScheduleReservationView,
    Client_ReservationView,
    Client_ReservationDetailView
)
from .v1.search import Client_SearchConsultantView

app_name = 'client'

urlpatterns = [
    path('issue/', Client_IssueView.as_view(), name='issue'),
    path('issue/<uuid:uuid>/', Client_IssueDetailView.as_view(), name='issue_detail'),
    path('search/consultant/', Client_SearchConsultantView.as_view(), name='search_consultant'),
    path('schedule-reservation/<uuid:uuid>/', Client_ScheduleReservationView.as_view(), name='schedule_reservation'),
    path('reservation/', Client_ReservationView.as_view(), name='reservation'),
    path('reservation/<uuid:uuid>/', Client_ReservationDetailView.as_view(), name='reservation_detail'),
    path('reservation/<uuid:uuid>/change/', Client_ReservationChangeView.as_view(), name='reservation_change'),
]
