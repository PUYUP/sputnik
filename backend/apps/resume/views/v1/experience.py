from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from utils.generals import choices_to_json
from utils.constants import MONTH_CHOICES
from apps.person.decorators import consultant_required
from ...utils.constants import EMPLOYMENT_CHOICES


@method_decorator([login_required, consultant_required], name='dispatch')
class ExperienceView(View):
    template_name = 'v1/resume/experience.html'
    context = dict()

    def get(self, request):
        self.context['employment_choices'] = choices_to_json(EMPLOYMENT_CHOICES)
        self.context['month_choices'] = choices_to_json(MONTH_CHOICES)
        return render(request, self.template_name, self.context)
