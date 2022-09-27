from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from apps.person.decorators import consultant_required


@method_decorator([login_required, consultant_required], name='dispatch')
class Consultant_DashboardView(View):
    template_name = 'v1/person/consultant/dashboard.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)
