from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from utils.generals import get_model, choices_to_json
from apps.person.utils.constants import GENDER_CHOICES, RRULE_WKST_CHOICES

Profile = get_model('person', 'Profile')
Account = get_model('person', 'Account')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'v1/person/user/profile.html'
    context = dict()

    def get(self, request):
        user = request.user
        profile = Profile.objects.get(user__uuid=user.uuid)

        self.context['profile'] = profile
        self.context['gender_choices'] = choices_to_json(GENDER_CHOICES)
        return render(request, self.template_name, self.context)


@method_decorator(login_required, name='dispatch')
class SecurityView(View):
    template_name = 'v1/person/user/security.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)


@method_decorator(login_required, name='dispatch')
class UserDetailView(View):
    template_name = 'v1/person/user/detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        self.context['wkst_choices'] = choices_to_json(RRULE_WKST_CHOICES)
        return render(request, self.template_name, self.context)
