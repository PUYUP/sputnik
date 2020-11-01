from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .issue.views import IssueAPIView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('issues', IssueAPIView, basename='issue')

app_name = 'client'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
