from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from apps.person.decorators import consultant_required


@method_decorator([login_required, consultant_required], name='dispatch')
class Consultant_ReservationView(View):
    template_name = 'v1/helpdesk/consultant/reservation.html'
    context = dict()

    def get(self, request, status=None):
        self.context['status'] = status
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        return render(request, self.template_name, self.context)


@method_decorator([login_required, consultant_required], name='dispatch')
class Consultant_ReservationDetailView(View):
    template_name = 'v1/helpdesk/consultant/reservation-detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        return render(request, self.template_name, self.context)
