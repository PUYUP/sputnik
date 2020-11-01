from django.urls import path

from .consultation import Client_ConsultationView, Client_ConsultationDetailView
from .search import Client_SearchConsultantView

app_name = 'client'

urlpatterns = [
    path('consultation/', Client_ConsultationView.as_view(), name='consultation'),
    path('consultation/<uuid:uuid>/', Client_ConsultationDetailView.as_view(), name='consultation_detail'),
    path('search/consultant/', Client_SearchConsultantView.as_view(), name='search_consultant'),
]
