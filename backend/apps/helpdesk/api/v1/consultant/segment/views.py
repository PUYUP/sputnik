from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import Prefetch
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework import serializers
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from utils.generals import get_model
from apps.helpdesk.api.v1.consultant.sla.serializers import SLASerializer
from apps.helpdesk.api.v1.consultant.segment.serializers import SegmentSerializer
from apps.helpdesk.api.v1.consultant.priority.serializers import PrioritySerializer
from apps.helpdesk.utils.permissions import IsConsultantOnly

Segment = get_model('helpdesk', 'Segment')
Priority = get_model('helpdesk', 'Priority')


class SegmentApiView(viewsets.ViewSet):
    """
    GET
    ---------------

    Format;

        {
            "schedule": "b2c76dda-bcd4-44e3-92a8-9a9bbb7edad9"
        }

    POST
    ---------------

    Format;

        {
            "schedule": "85eab55d-9466-4029-8725-10405d5594cd",
            "open_hour": "08:00:00",
            "close_hour": "10:00:00",
            "max_opened": 5,
            "is_active": true
        }

    PATCH
    ---------------

    Format;

        {
            "open_hour": "08:00:00",
            "close_hour": "10:00:00",
            "max_opened": 5,
            "is_active": true
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def get_object(self, uuid=None, is_update=False):
        queryset = Segment.objects \
            .prefetch_related(Prefetch('slas'), Prefetch('user'), Prefetch('schedule')) \
            .select_related('user', 'schedule')

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = queryset.get(uuid=uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def get_objects(self, schedule_uuid=None):
        user = self.request.user
        queryset = Segment.objects

        # If current user not creator show only PUBLISH status
        try:
            queryset = queryset.prefetch_related(Prefetch('schedule'), Prefetch('user')) \
                .select_related('schedule', 'user') \
                .filter(user__uuid=user.uuid, schedule__uuid=schedule_uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        query_params = request.query_params
        schedule_uuid = query_params.get('schedule_uuid')

        queryset = self.get_objects(schedule_uuid=schedule_uuid)
        serializer = SegmentSerializer(queryset, many=True, context=context,
                                       fields=('url', 'canal', 'open_hour', 'close_hour',
                                               'max_opened', 'is_active', 'uuid',))
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = SegmentSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    @method_decorator(never_cache)
    def create(self, request, format=None):
        context = {'request': request}
        serializer = SegmentSerializer(data=request.data, context=context)
        if serializer.is_valid():
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable({'detail': repr(e)})
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    @method_decorator(never_cache)
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)
        serializer = SegmentSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid():
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable({'detail': repr(e)})
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    @method_decorator(never_cache)
    def destroy(self, request, uuid=None, format=None):
        # single object
        queryset = self.get_object(uuid=uuid)
        if queryset.user.uuid != request.user.uuid:
            raise NotAcceptable()

        # execute delete
        queryset.delete()
        return Response(
            {'detail': _("Delete success!")},
            status=response_status.HTTP_204_NO_CONTENT)
