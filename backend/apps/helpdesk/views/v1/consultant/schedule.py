from django.db.models import Prefetch, F
from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.serializers import serialize

from apps.person.decorators import consultant_required
from apps.helpdesk.utils.constants import RRULE_FREQ_CHOICES, RRULE_WKST_CHOICES
from utils.generals import choices_to_json, get_model

Expertise = get_model('resume', 'Expertise')


@method_decorator([login_required, consultant_required], name='dispatch')
class Consultant_ScheduleView(View):
    template_name = 'v1/helpdesk/consultant/schedule.html'
    context = dict()

    def get(self, request):
        self.context['freq_choices'] = choices_to_json(RRULE_FREQ_CHOICES)
        self.context['wkst_choices'] = choices_to_json(RRULE_WKST_CHOICES)
        return render(request, self.template_name, self.context)


@method_decorator([login_required, consultant_required], name='dispatch')
class Consultant_ScheduleDetailView(View):
    template_name = 'v1/helpdesk/consultant/schedule-detail.html'
    context = dict()

    def get(self, request, uuid=None):
        self.context['uuid'] = uuid
        self.context['wkst_choices'] = choices_to_json(RRULE_WKST_CHOICES)
        return render(request, self.template_name, self.context)