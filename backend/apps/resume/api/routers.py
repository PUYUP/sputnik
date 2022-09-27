from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .expertise.v1.views import ExpertiseApiView
from .education.v1.views import EducationApiView
from .experience.v1.views import ExperienceApiView
from .certificate.v1.views import CertificateApiView
from .attachment.v1.views import AttachmentApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('expertises', ExpertiseApiView, basename='expertise')
router.register('educations', EducationApiView, basename='education')
router.register('experiences', ExperienceApiView, basename='experience')
router.register('certificates', CertificateApiView, basename='certificate')
router.register('attachments', AttachmentApiView, basename='attachment')

app_name = 'resume'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]
