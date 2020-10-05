from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .skill.views import SkillApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('skills', SkillApiView, basename='skill')

app_name = 'master'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
