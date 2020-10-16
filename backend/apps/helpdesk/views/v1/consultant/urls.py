from django.urls import path

from .schedule import Consultant_ScheduleView, Consultant_ScheduleDetailView

app_name = 'consultant'

urlpatterns = [
    path('schedule/', Consultant_ScheduleView.as_view(), name='schedule'),
    path('schedule/<uuid:uuid>/', Consultant_ScheduleDetailView.as_view(), name='schedule_detail'),
]
