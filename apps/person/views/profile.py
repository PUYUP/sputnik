from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from utils.generals import get_model, choices_to_json
from apps.person.utils.constants import GENDER_CHOICES

Profile = get_model('person', 'Profile')
Account = get_model('person', 'Account')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'profile.html'
    context = dict()

    def get(self, request):
        user = request.user
        profile = Profile.objects.get(user__uuid=user.uuid)

        self.context['profile'] = profile
        self.context['gender_choices'] = choices_to_json(GENDER_CHOICES)
        return render(request, self.template_name, self.context)
