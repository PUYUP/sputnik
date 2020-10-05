from django.urls import path

from .base import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home')
]
