from django.urls import path

from .v1.education import EducationView
from .v1.experience import ExperienceView
from .v1.certificate import CertificateView
from .v1.expertise import ExpertiseView

app_name = 'resume_view'

urlpatterns = [
    path('education/', EducationView.as_view(), name='education'),
    path('experience/', ExperienceView.as_view(), name='experience'),
    path('certificate/', CertificateView.as_view(), name='certificate'),
    path('expertise/', ExpertiseView.as_view(), name='expertise'),
]
