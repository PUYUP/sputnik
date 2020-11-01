from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

_APP_VERSION = settings.APP_VERSION_SLUG

from apps.person.decorators import client_required


@method_decorator([login_required, client_required], name='dispatch')
class Client_ConsultationView(View):
    template_name = _APP_VERSION + '/helpdesk/client/consultation.html'
    context = dict()

    def get(self, request):
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_ConsultationDetailView(View):
    template_name = _APP_VERSION + '/helpdesk/client/consultation-detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        return render(request, self.template_name, self.context)
