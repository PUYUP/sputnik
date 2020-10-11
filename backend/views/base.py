from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.views import View
from django.shortcuts import redirect, render

from utils.generals import get_model
from apps.person.utils.constants import CLIENT, CONSULTANT

Attribute = get_model('helpdesk', 'Attribute')
Schedule = get_model('helpdesk', 'Schedule')


class HomeView(View):
    template_name = settings.APP_VERSION_SLUG + '/base/home.html'
    context = dict()

    def get(self, request):
        attr = Attribute.objects.get(id=1)
        content_object = Schedule.objects.get(id=1)
        
        # set new attribute
        # attr.save_value(content_object, 'WE')
        # or
        # attr.save_value(content_object, 'WE', 'Ingored')

        # update attribute value from WE to MO
        # attr.save_value(content_object, 'TU', 'SA')

        # attr.save_value(content_object, 'SU', 'MO')

        # delete attribute
        # find the value want to delete
        # attr.save_value(content_object, 'TU', 'SA', deleted=True)
        attr.save_value(content_object, 'WE', 'SA', deleted=True)

        print(content_object)

        if self.request.user.is_authenticated:
            roles = request.user.roles_identifier()
            if CLIENT in roles:
                pass
            elif CONSULTANT in roles:
                return redirect(reverse('person_view:consultant:dashboard'))
        return render(request, self.template_name, self.context)
