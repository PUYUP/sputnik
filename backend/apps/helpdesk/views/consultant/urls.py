from django.urls import path

from .v1.schedule import (
    Consultant_ScheduleView, 
    Consultant_ScheduleDetailView,
    Consultant_ScheduleCalendarView
)
from .v1.consultation import (
    Consultant_ReservationView,
    Consultant_ReservationDetailView
)

app_name = 'consultant'

urlpatterns = [
    path('schedule/', Consultant_ScheduleView.as_view(), name='schedule'),
    path('schedule/<uuid:uuid>/', Consultant_ScheduleDetailView.as_view(), name='schedule_detail'),
    path('schedule/<uuid:uuid>/calendar/', Consultant_ScheduleCalendarView.as_view(), name='schedule_calendar'),
    path('reservation/', Consultant_ReservationView.as_view(), name='reservation'),
    path('reservation/<uuid:uuid>/', Consultant_ReservationDetailView.as_view(), name='reservation_detail'),
]
