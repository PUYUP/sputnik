from django.urls import path

from .dashboard import Client_DashboardView

app_name = 'client'

urlpatterns = [
    path('', Client_DashboardView.as_view(), name='dashboard'),
]
