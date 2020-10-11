from django.db.models import Q, Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from .serializers import TopicSerializer

Topic = get_model('master', 'Topic')


class TopicApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Params:
        {
            "s": "string"
        }

    Example:
        api/master/topics/?s=PHP
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
    
        queryset = Topic.objects \
            .prefetch_related(Prefetch('scopes')) \
            .filter(Q(is_active=True), Q(label__icontains=s))
        serializer = TopicSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
