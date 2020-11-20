from django.urls import path, include
from django.contrib.auth import views as auth_views

from .consultant import urls as consultant_urls
from .client import urls as client_urls

app_name = 'helpdesk_view'

urlpatterns = [
    path('consultant/', include(consultant_urls, namespace='consultant')),
    path('client/', include(client_urls, namespace='client')),
]
