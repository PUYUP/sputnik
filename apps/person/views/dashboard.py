from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    template_name = 'person/dashboard.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)
