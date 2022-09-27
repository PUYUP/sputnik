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
                    'schedulesterm': reverse('helpdesk_api:consultant:scheduleterm-list', request=request,
                                             format=format, current_app='helpdesk_api:consultant'),
                    'rules': reverse('helpdesk_api:consultant:rule-list', request=request,
                                     format=format, current_app='helpdesk_api:consultant'),
                    'rulesvalue': reverse('helpdesk_api:consultant:rulevalue-list', request=request,
                                          format=format, current_app='helpdesk_api:consultant'),
                    'segments': reverse('helpdesk_api:consultant:segment-list', request=request,
                                        format=format, current_app='helpdesk_api:consultant'),
                    'slas': reverse('helpdesk_api:consultant:sla-list', request=request,
                                    format=format, current_app='helpdesk_api:consultant'),
                    'priorities': reverse('helpdesk_api:consultant:priority-list', request=request,
                                          format=format, current_app='helpdesk_api:consultant'),
                    'reservations': reverse('helpdesk_api:consultant:reservation-list', request=request,
                                            format=format, current_app='helpdesk_api:consultant'),
                    'assigns': reverse('helpdesk_api:consultant:assign-list', request=request,
                                       format=format, current_app='helpdesk_api:consultant'),
                },
                'client': {
                    'issues': reverse('helpdesk_api:client:issue-list', request=request,
                                      format=format, current_app='helpdesk_api:client'),
                    'reservations': reverse('helpdesk_api:client:reservation-list', request=request,
                                            format=format, current_app='helpdesk_api:client'),
                    'reservationsitem': reverse('helpdesk_api:client:reservation_item-list', request=request,
                                                format=format, current_app='helpdesk_api:client'),
                }
            }
        })
