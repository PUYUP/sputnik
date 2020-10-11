from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .consultant import routers as consultant_routers

app_name = 'helpdesk_api'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('consultant/', include(consultant_routers)),
]
