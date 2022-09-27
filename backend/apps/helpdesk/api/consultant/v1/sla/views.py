from django.db.models import Prefetch
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
from apps.helpdesk.utils.permissions import (
    IsConsultantOnly, 
    IsObjectOwnerOrReject, 
    IsResumeCompleteOrReject
)
from .serializers import SLASerializer

SLA = get_model('helpdesk', 'SLA')


class SLAApiView(viewsets.ViewSet):
    """
    GET
    ---------------

    Format;

        {
            "segment": "b2c76dda-bcd4-44e3-92a8-9a9bbb7edad9"
        }

    POST
    ---------------

    Format;

        {
            "segment": "85eab55d-9466-4029-8725-10405d5594cd",
            "label": "abc",
            "description": null,
            "promise": "saa",
            "grace_periode": 10,
            "cost": 10000,
            "is_active": true,
            "priority": [
                {"identifier": "high", "label": "Penting", "cost": 1000}
            ]
        }

    PATCH
    ---------------

    Format;

        {
            "label": "abc",
            "description": null,
            "promise": "saa",
            "grace_periode": 10,
            "cost": 10000,
            "is_active": true,
            "priority": [
                {"uuid": "uuid.v4", "identifier": "high", "label": "Penting", "cost": 1000}
            ]
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
        q = SLA.objects \
            .prefetch_related(Prefetch('user'), Prefetch('segment')) \
            .select_related('user', 'segment')
        return q

    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def get_objects(self, segment_uuid=None):
        try:
            queryset = self.queryset.prefetch_related(Prefetch('schedule'), Prefetch('priority'),
                                                 Prefetch('user'), Prefetch('segment')) \
                .select_related('schedule', 'segment', 'user') \
                .filter(user__uuid=self.user.uuid, segment__uuid=segment_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        segment_uuid = request.query_params.get('segment_uuid')
        if not segment_uuid:
            raise NotAcceptable({'segment_uuid': _("Param segment_uuid required!")})

        queryset = self.get_objects(segment_uuid=segment_uuid)
        serializer = SLASerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = SLASerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    @method_decorator(never_cache)
    def create(self, request, format=None):
        context = {'request': request}
        serializer = SLASerializer(data=request.data, context=context)
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
    
        serializer = SLASerializer(queryset, data=request.data, partial=True, context=context)
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
