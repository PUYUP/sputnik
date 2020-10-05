from django.urls import path

from .dashboard import Consultant_DashboardView

app_name = 'consultant'

urlpatterns = [
    path('', Consultant_DashboardView.as_view(), name='dashboard'),
]
