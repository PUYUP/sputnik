# THIRD PARTY
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'person': {
                'token': reverse('person:token_obtain_pair', request=request,
                                 format=format, current_app='person'),
                'token-refresh': reverse('person:token_refresh', request=request,
                                         format=format, current_app='person'),
                'users': reverse('person:user-list', request=request,
                                 format=format, current_app='person'),
                'otps': reverse('person:otp-list', request=request,
                                format=format, current_app='person'),
                'educations': reverse('person:education-list', request=request,
                                      format=format, current_app='person'),
                'experiences': reverse('person:experience-list', request=request,
                                       format=format, current_app='person'),
                'certificates': reverse('person:certificate-list', request=request,
                                        format=format, current_app='person'),
            },
            'helpdesk': {
                'base': {
                    'topics': reverse('helpdesk:topic-list', request=request,
                                      format=format, current_app='helpdesk'),
                },
                'expert': {
                    'experts': reverse('helpdesk:expert-list', request=request,
                                       format=format, current_app='helpdesk'),
                    'expertises': reverse('helpdesk:expertise-list', request=request,
                                          format=format, current_app='helpdesk'),
                    'schedules': reverse('helpdesk:schedule-list', request=request,
                                         format=format, current_app='helpdesk'),
                }
            }
        })
