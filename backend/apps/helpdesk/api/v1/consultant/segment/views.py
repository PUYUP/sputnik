from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import Prefetch
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from apps.helpdesk.api.v1.consultant.segment.serializers import SegmentSerializer
from apps.helpdesk.utils.permissions import IsConsultantOnly, IsObjectOwnerOrReject, IsResumeCompleteOrReject

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
    permission_classes = (IsAuthenticated, IsConsultantOnly, IsResumeCompleteOrReject,)
    permission_action = {
        'partial_update': [IsAuthenticated, IsObjectOwnerOrReject],
        'destroy': [IsAuthenticated, IsObjectOwnerOrReject],
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action
                    [self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def initialize_request(self, request, *args, **kwargs):
        self.user = request.user
        return super().initialize_request(request, *args, **kwargs)

    @property
    def queryset(self):
        q = Segment.objects \
            .prefetch_related(Prefetch('sla'), Prefetch('user'), Prefetch('schedule')) \
            .select_related('user', 'schedule')
        return q

    # single object
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    # multiple objects
    def get_objects(self, schedule_uuid=None):
        try:
            queryset = self.queryset \
                .filter(user__uuid=self.user.uuid, schedule__uuid=schedule_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        schedule_uuid = request.query_params.get('schedule_uuid')

        queryset = self.get_objects(schedule_uuid=schedule_uuid)
        serializer = SegmentSerializer(queryset, many=True, context=context,
                                       fields_used=('url', 'canal', 'open_hour', 'close_hour',
                                                    'max_opened', 'is_active', 'uuid', 'quota',))
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
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    @method_decorator(never_cache)
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = SegmentSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    @method_decorator(never_cache)
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)
        
        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
