from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, Value
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from utils.generals import get_model
from apps.person.utils.auth import GuestRequiredMixin, clear_otp_session
from apps.person.utils.constants import (
    REGISTER_VALIDATION,
    PASSWORD_RECOVERY
)
from apps.person.forms import RegisterForm, SetPasswordForm

User = get_model('person', 'User')
OTPFactory = get_model('person', 'OTPFactory')


class BoardingView(GuestRequiredMixin, View):
    template_name = 'person/auth/boarding.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


class ValidateOTPFactoryView(GuestRequiredMixin, View):
    template_name = 'person/auth/validate-otp.html'
    context = dict()
    otp_email, otp_msisdn, token, otp_challenge, otp_obj = [None] * 5

    def dispatch(self, *args, **kwargs):
        self.opt_uuid = self.request.session.get('otp_request_uuid', None)
        self.otp_email = self.request.session.get('otp_request_email', None)
        self.otp_msisdn = self.request.session.get('otp_request_msisdn', None)
        self.otp_token = self.request.session.get('otp_request_token', None)
        self.otp_challenge = self.request.session.get('otp_request_challenge', None)
        self.otp_send_to_message = self.request.session.get('otp_request_send_to_message', None)

        # redirect to
        self.otp_redirect_to = reverse('person_otp_validation') # default
        if self.otp_challenge == PASSWORD_RECOVERY:
            self.otp_redirect_to = reverse('person_password_recovery')
        
        if self.otp_challenge == REGISTER_VALIDATION:
            self.otp_redirect_to = reverse('person_register')

        if (not self.otp_email and not self.otp_msisdn) or not self.otp_token or not self.otp_challenge:
            return redirect(reverse('home'))

        # make sure otp valid!
        with transaction.atomic():
            self.get_otp()
        return super().dispatch(*args, **kwargs)

    def get_otp(self):
        try:
            obj = OTPFactory.objects.select_for_update()\
                .get_unverified_unused(email=self.otp_email, msisdn=self.otp_msisdn,
                                       token=self.otp_token, challenge=self.otp_challenge)
            return obj
        except ObjectDoesNotExist:
            # redirect to depend page
            if otp_challenge == REGISTER_VALIDATION:
                return redirect(reverse('person_boarding'))

            if otp_challenge == PASSWORD_RECOVERY:
                return redirect(reverse('person_lost_password'))

    def get(self, request):
        self.context['send_to_message'] = self.otp_send_to_message
        self.context['redirect_to'] = self.otp_redirect_to
        self.context['challenge'] = self.otp_challenge
        return render(request, self.template_name, self.context)


class RegisterView(GuestRequiredMixin, View):
    template_name = 'person/auth/register.html'
    form = RegisterForm
    context = dict()
    otp_email, otp_msisdn, token, otp_challenge, otp_obj = [None] * 5

    def dispatch(self, *args, **kwargs):
        self.otp_token = self.request.session.get('otp_validate_token', None)
        self.otp_email = self.request.session.get('otp_validate_email', None)
        self.otp_msisdn = self.request.session.get('otp_validate_msisdn', None)

        if not self.otp_token and (not self.otp_email or not self.otp_msisdn):
            return redirect(reverse('person_boarding'))

        # make sure registration otp valid!
        with transaction.atomic():
            self.otp_obj = self.get_otp()
        return super().dispatch(*args, **kwargs)

    def get_otp(self):
        try:
            obj = OTPFactory.objects.select_for_update() \
                .get_verified_unused(email=self.otp_email, msisdn=self.otp_msisdn,
                                     token=self.otp_token, challenge=REGISTER_VALIDATION)
            return obj
        except ObjectDoesNotExist:
            return redirect(reverse('person_boarding'))

    def get(self, request):
        self.context['form'] = self.form(request=request)
        return render(request, self.template_name, self.context)

    @transaction.atomic
    def post(self, request):
        form = self.form(request.POST, request=request)
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name', None)
            username = form.cleaned_data.get('username', None)
            email = form.cleaned_data.get('email', None)
            password = form.cleaned_data.get('password2', None)

            try:
                user = User.objects.create_user(username, email, password,
                                                first_name=first_name)
            except IntegrityError as e:
                return redirect(reverse('person_register'))

            # then login user
            user_auth = authenticate(request, username=username, password=password)
            if user_auth is not None:
                login(request, user_auth)

            # clear otp validate session
            clear_otp_session(request, 'validate')

            # mark otp used
            self.otp_obj.mark_used()

            # refresh live to dashboard
            return redirect(reverse('home'))

        self.context['form'] = form
        return render(request, self.template_name, self.context)


class LoginView(GuestRequiredMixin, View):
    template_name = 'auth/login.html'
    context = dict()

    def get(self, request):
        self.context['messages'] = messages.get_messages(request)
        return render(request, self.template_name, self.context)

    @transaction.atomic
    def post(self, request):
        # Placehoder only if user submit the form. Not realy use
        return render(request, self.template_name, self.context)


class LostPasswordView(GuestRequiredMixin, View):
    template_name = 'person/auth/lost-password.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)

    @transaction.atomic
    def post(self, request):
        # Placehoder only if user submit the form. Not realy use
        return render(request, self.template_name, self.context)


class LostPasswordConfirmView(GuestRequiredMixin, View):
    template_name = 'person/auth/lost-password-recovery.html'
    form = SetPasswordForm
    context = dict()
    otp_email, otp_msisdn, token, otp_challenge, otp_obj = [None] * 5

    def dispatch(self, *args, **kwargs):
        self.otp_token = self.request.session.get('otp_validate_token', None)
        self.otp_email = self.request.session.get('otp_validate_email', None)
        self.otp_msisdn = self.request.session.get('otp_validate_msisdn', None)

        if not self.otp_token and (not self.otp_email or not self.otp_msisdn):
            return redirect(reverse('person_lost_password'))

        # make sure registration otp verified!
        with transaction.atomic():
            self.otp_obj = self.get_otp()

        user, isvalid = self.get_user(self.request)
        if user.email != self.otp_email:
            return redirect(reverse('person_lost_password'))
        return super().dispatch(*args, **kwargs)

    def get_otp(self):
        try:
            obj = OTPFactory.objects.select_for_update() \
                .get_verified_unused(email=self.otp_email, msisdn=self.otp_msisdn,
                                     token=self.otp_token, challenge=PASSWORD_RECOVERY)
            return obj
        except ObjectDoesNotExist:
            return redirect(reverse('person_lost_password'))

    def get_user(self, request):
        token = self.request.session.get('password_recovery_token', None)
        uidb64 = self.request.session.get('password_recovery_uidb64', None)

        # check password recovery valid or not
        uid = urlsafe_base64_decode(uidb64).decode()
        try:
            user = User._default_manager.get(pk=uid)
        except ObjectDoesNotExist:
            return redirect(reverse('home'))

        isvalid = default_token_generator.check_token(user, token)
        return user, isvalid;

    def get(self, request):
        user, isvalid = self.get_user(request)

        self.context['otp_email'] = self.otp_email
        self.context['isvalid'] = isvalid
        self.context['form'] = self.form(user)
        return render(request, self.template_name, self.context)

    @transaction.atomic
    def post(self, request):
        # Placehoder only if user submit the form. Not realy use
        user, isvalid = self.get_user(request)
        form = self.form(user, request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, _("Kata sandi berhasil dirubah."
                                        " Login dengan kata sandi baru Anda."))

            # clear otp session
            clear_otp_session(request, 'validate')

            # mark otp used
            self.otp_obj.mark_used()

            # clear password recovery session
            otp_keys = ['password_recovery_token', 'password_recovery_uidb64']
            for key in otp_keys:
                try:
                    del request.session[key]
                except KeyError:
                    pass
                    
            # back to login
            return redirect(reverse('person_login'))

        self.context['otp_email'] = user.email
        self.context['form'] = form
        self.context['isvalid'] = isvalid
        return render(request, self.template_name, self.context)
