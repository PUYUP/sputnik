from django.urls import path

from .v1.dashboard import Client_DashboardView

app_name = 'client'

urlpatterns = [
    path('', Client_DashboardView.as_view(), name='dashboard'),
]
