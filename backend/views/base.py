from django.urls import reverse
from django.conf import settings
from django.views import View
from django.shortcuts import redirect, render

from apps.person.utils.constants import CLIENT, CONSULTANT


class HomeView(View):
    template_name = settings.APP_VERSION_SLUG + '/base/home.html'
    context = dict()

    def get(self, request):
        if self.request.user.is_authenticated:
            roles = request.user.roles_identifier()
            if CLIENT in roles:
                pass
            elif CONSULTANT in roles:
                return redirect(reverse('person_view:consultant:dashboard'))
        return render(request, self.template_name, self.context)
