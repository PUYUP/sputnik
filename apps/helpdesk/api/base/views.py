from django.db.models import Prefetch, Q
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from apps.helpdesk.api.base.serializers import TopicSerializer

Topic = get_model('helpdesk', 'Topic')
Expertise = get_model('helpdesk', 'Expertise')


class TopicApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Params:
        {
            "s": "string"
        }

    Example:
        api/helpdesk/topics/?s=PHP
    """
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)

    def list(self, request, format=None):
        params_missed = dict()
        context = {'request': request}
        s = request.query_params.get('s')

        if not s:
            params_missed.update({'s': _("Required")})

        # print error if params not provided
        if params_missed:
            raise NotAcceptable(detail=params_missed)
    
        excludes = Expertise.objects \
            .prefetch_related(Prefetch('topic'), Prefetch('user')) \
            .select_related('topic', 'user') \
            .filter(topic__subject__icontains=s, user_id=request.user.id) \
            .values_list('topic__id', flat=True)

        queryset = Topic.objects.filter(is_active=True, subject__icontains=s) \
            .exclude(id__in=excludes)
        serializer = TopicSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
