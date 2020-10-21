# THIRD PARTY
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'master': {
                'topics': reverse('master:topic-list', request=request,
                                  format=format, current_app='master')
            },
            'person': {
                'token': reverse('person_api:token_obtain_pair', request=request,
                                 format=format, current_app='person_api'),
                'token-refresh': reverse('person_api:token_refresh', request=request,
                                         format=format, current_app='person_api'),
                'users': reverse('person_api:user-list', request=request,
                                 format=format, current_app='person_api'),
                'verifycodes': reverse('person_api:verifycode-list', request=request,
                                format=format, current_app='person_api'),
            },
            'resume': {
                'educations': reverse('resume:education-list', request=request,
                                      format=format, current_app='resume'),
                'experiences': reverse('resume:experience-list', request=request,
                                       format=format, current_app='resume'),
                'certificates': reverse('resume:certificate-list', request=request,
                                        format=format, current_app='resume'),
                'expertises': reverse('resume:expertise-list', request=request,
                                      format=format, current_app='resume'),
                'attachments': reverse('resume:attachment-list', request=request,
                                       format=format, current_app='resume'),
            },
            'helpdesk': {
                'consultant': {
                    'schedules': reverse('helpdesk_api:consultant:schedule-list', request=request,
                                         format=format, current_app='helpdesk_api:consultant'),
                    'recurrences': reverse('helpdesk_api:consultant:recurrence-list', request=request,
                                           format=format, current_app='helpdesk_api:consultant'),
                    'rules': reverse('helpdesk_api:consultant:rule-list', request=request,
                                     format=format, current_app='helpdesk_api:consultant'),
                    'segments': reverse('helpdesk_api:consultant:segment-list', request=request,
                                        format=format, current_app='helpdesk_api:consultant'),
                    'slas': reverse('helpdesk_api:consultant:sla-list', request=request,
                                    format=format, current_app='helpdesk_api:consultant'),
                }
            }
        })
