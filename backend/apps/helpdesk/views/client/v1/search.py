from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from apps.person.decorators import client_required


@method_decorator([login_required, client_required], name='dispatch')
class Client_SearchConsultantView(View):
    template_name = 'v1/helpdesk/client/search-consultant.html'
    context = dict()

    def get(self, request):
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        return render(request, self.template_name, self.context)
