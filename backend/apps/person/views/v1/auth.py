from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from utils.generals import get_model
from apps.person.utils.auth import GuestRequiredMixin

User = get_model('person', 'User')
VerifyCode = get_model('person', 'VerifyCode')


# REGISTER
class RegisterView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/register.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# REGISTER CAPTURE DATA
class RegisterCaptureView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/register-capture.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# BOARDING
class LoginView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/login.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# BOARDING PASSWORD
class LoginPasswordView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/login-password.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# LOST PASSWORD
class LostPasswordView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/lost-password.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# PASSWORD RECOVERY
class LostPasswordRecoveryView(GuestRequiredMixin, View):
    template_name = 'v1/person/auth/lost-password-recovery.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


# VERIFYCODE VALIDATION
class VerifyCodeView(View):
    template_name = 'v1/person/auth/verifycode-validation.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)
