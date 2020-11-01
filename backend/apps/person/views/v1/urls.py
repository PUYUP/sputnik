from django.urls import path, include
from django.contrib.auth import views as auth_views

from .consultant import urls as consultant_urls
from .client import urls as client_urls
from .user import ProfileView, SecurityView, UserDetailView
from .auth import (
    LoginPasswordView, LostPasswordRecoveryView, RegisterCaptureView,
    RegisterView, LoginView, LostPasswordView, VerifyCodeView
)

app_name = 'person_view'

urlpatterns = [
    # BOTH CONSULTANT and CLIENT USED THIS
    path('login/', LoginView.as_view(), name='login'),
    path('login/password/', LoginPasswordView.as_view(), name='login_password'),
    path('verifycode-validation/', VerifyCodeView.as_view(), name='verifycode_validate'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('lost-password/', LostPasswordView.as_view(), name='lost_password'),
    path('lost-password/recovery/', LostPasswordRecoveryView.as_view(), name='lost_password_recovery'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register/capture/', RegisterCaptureView.as_view(), name='register_capture'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('security/', SecurityView.as_view(), name='security'),
    path('<uuid:uuid>/', UserDetailView.as_view(), name='user_detail'),

    # CONSULTANT URL's
    path('consultant/', include(consultant_urls, namespace='consultant')),

    # CLIENT URL's
    path('client/', include(client_urls, namespace='client')),
]
