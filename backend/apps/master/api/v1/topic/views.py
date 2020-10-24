from django.db import transaction
from django.db.models import Q, Prefetch
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, ValidationError

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
    
    POST
    --------------------

    Params;

        {
            "label": "PHP",
            "description": "A server language"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (AllowAny, IsAuthenticated,)

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

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = TopicSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)
