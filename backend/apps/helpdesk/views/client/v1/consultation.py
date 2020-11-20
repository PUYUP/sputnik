from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from apps.person.decorators import client_required


@method_decorator([login_required, client_required], name='dispatch')
class Client_ScheduleReservationView(View):
    template_name = 'v1/helpdesk/client/schedule-reservation.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid # schedule.uuid
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_IssueView(View):
    template_name = 'v1/helpdesk/client/issue.html'
    context = dict()

    def get(self, request):
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_IssueDetailView(View):
    template_name = 'v1/helpdesk/client/issue-detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_ReservationView(View):
    template_name = 'v1/helpdesk/client/reservation.html'
    context = dict()

    def get(self, request, status=None):
        self.context['status'] = status
        self.context['per_page'] = settings.PAGINATION_PER_PAGE
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_ReservationDetailView(View):
    template_name = 'v1/helpdesk/client/reservation-detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        return render(request, self.template_name, self.context)


@method_decorator([login_required, client_required], name='dispatch')
class Client_ReservationChangeView(View):
    template_name = 'v1/helpdesk/client/reservation-change.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        return render(request, self.template_name, self.context)
