from apps.resume.utils.constants import EXPERTISE_LEVELS
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from utils.generals import choices_to_json
from apps.person.decorators import consultant_required


@method_decorator([login_required, consultant_required], name='dispatch')
class ExpertiseView(View):
    template_name = 'v1/resume/expertise.html'
    context = dict()

    def get(self, request):
        self.context['expertise_levels'] = choices_to_json(EXPERTISE_LEVELS)
        return render(request, self.template_name, self.context)
