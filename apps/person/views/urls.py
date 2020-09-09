from django.urls import path, include
from django.contrib.auth import views as auth_views

from apps.person.views.auth import (
    BoardingView,
    ValidateOTPFactoryView,
    RegisterView,
    LoginView,
    LostPasswordView,
    LostPasswordConfirmView,
)
from apps.person.views.dashboard import DashboardView
from apps.person.views.profile import ProfileView

urlpatterns = [
    path('login/', LoginView.as_view(), name='person_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='person_logout'),
    path('boarding/', BoardingView.as_view(), name='person_boarding'),
    path('register/', RegisterView.as_view(), name='person_register'),
    path('otp-validation/', ValidateOTPFactoryView.as_view(), name='person_otp_validation'),
    path('lost-password/', LostPasswordView.as_view(), name='person_lost_password'),
    path('lost-password-recovery/', LostPasswordConfirmView.as_view(),
         name='person_password_recovery'),
    path('dashboard/', DashboardView.as_view(), name='person_dashboard'),
    path('profile/', ProfileView.as_view(), name='person_profile'),
]
