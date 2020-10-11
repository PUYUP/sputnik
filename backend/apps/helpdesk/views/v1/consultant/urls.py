from django.urls import path

from .schedule import Consultant_ScheduleView

app_name = 'consultant'

urlpatterns = [
    path('schedule/', Consultant_ScheduleView.as_view(), name='schedule'),
]
