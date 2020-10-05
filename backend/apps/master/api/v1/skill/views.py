from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from .serializers import SkillSerializer

Skill = get_model('master', 'Skill')


class SkillApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Params:
        {
            "s": "string"
        }

    Example:
        api/master/skills/?s=PHP
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
    
        queryset = Skill.objects \
            .prefetch_related(Prefetch('scope')) \
            .select_related('scope') \
            .filter(is_active=True, label__icontains=s)
        serializer = SkillSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
