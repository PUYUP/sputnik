from django.urls import path

from .v1.dashboard import Consultant_DashboardView

app_name = 'consultant'

urlpatterns = [
    path('', Consultant_DashboardView.as_view(), name='dashboard'),
]
