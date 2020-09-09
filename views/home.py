from django.views import View
from django.shortcuts import render

from dateutil import rrule
import datetime

from utils.generals import get_model
from apps.helpdesk.utils.constants import WKST_CHOICES, FREQ_CHOICES


class HomeView(View):
    template_name = 'global/home.html'
    context = dict()

    def get(self, request):
        """
        x = '1,2,8'

        # clean whitespace
        y = x.replace(' ', '')

        # to list
        z = y.split(',')
        
        # get different value
        wkst_list = list(dict(WKST_CHOICES).keys())
        a = list(set(z) - set(wkst_list))

        if a:
            print(a)

        from pprint import pprint
        pprint(rrule.__dict__)

        # pprint(rrule.FREQNAMES)
        print(rrule.MO.__dict__)
        print(rrule.weekdaybase(2))
        print(rrule.weekdays)
        print(rrule.WEEKLY)

        print(list(dict(FREQ_CHOICES).keys()))

        print(11 in dict(FREQ_CHOICES))
        print(datetime.date(2017,12,15).weekday(), 'DD')
        """

        roles = ['ac']
        print(roles)

        return render(request, self.template_name, self.context)
