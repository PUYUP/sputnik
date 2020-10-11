from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .topic.views import TopicApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('topics', TopicApiView, basename='topic')

app_name = 'master'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
