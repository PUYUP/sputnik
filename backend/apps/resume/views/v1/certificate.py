from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from utils.generals import choices_to_json
from utils.constants import MONTH_CHOICES
from apps.person.decorators import consultant_required


@method_decorator([login_required, consultant_required], name='dispatch')
class CertificateView(View):
    template_name = 'v1/resume/certificate.html'
    context = dict()

    def get(self, request):
        self.context['month_choices'] = choices_to_json(MONTH_CHOICES)
        return render(request, self.template_name, self.context)
