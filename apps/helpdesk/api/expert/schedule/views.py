from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, ValidationError
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from apps.helpdesk.api.expert.schedule.serializers import ScheduleSerializer

Schedule = get_model('helpdesk', 'Schedule')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ScheduleApiView(viewsets.ViewSet):
    """
    POST
    ------------------
        {
            "expertise": [12,2],
            "label": "string",
            "dtstart": "datetime"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        response = dict()
        response['count'] = _PAGINATOR.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'offset': _PAGINATOR.offset,
            'limit': _PAGINATOR.limit,
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
        }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        context = {'request': request}
        user_uuid = request.query_params.get('user_uuid') # :user uuid

        queryset = Schedule.objects \
            .prefetch_related(Prefetch('user'), Prefetch('expertise'), Prefetch('expertise__topic')) \
            .select_related('user')

        # access as public only show active schedules
        if (user_uuid):
            queryset = queryset.filter(user__uuid=user_uuid) \
                .exclude(~Q(user__uuid=request.user.uuid) & ~Q(is_active=True))
        else:
            queryset = queryset.filter(user_id=request.user.id)
    
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ScheduleSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ScheduleSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            except IntegrityError:
                return Response({'detail': _(u"Jadwal ini telah ditambahkan")},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
