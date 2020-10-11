from django.urls import path

from .education import EducationView
from .experience import ExperienceView
from .certificate import CertificateView
from .expertise import ExpertiseView

app_name = 'resume_view'

urlpatterns = [
    path('education/', EducationView.as_view(), name='education'),
    path('experience/', ExperienceView.as_view(), name='experience'),
    path('certificate/', CertificateView.as_view(), name='certificate'),
    path('expertise/', ExpertiseView.as_view(), name='expertise'),
]
