from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.pagination import build_result_pagination
from apps.helpdesk.utils.constants import PULL, PUSH, WAITING
from apps.helpdesk.utils.permissions import (
    IsClientOnly,
    IsReservationItemOwnerOrReject, 
    IsReservationOwnerOrReject
)

from .serializers import (
    ReservationItemCreateSerializer, 
    ReservationItemRetrieveSerializer,
    ReservationItemListSerializer,
    ReservationRetrieveSerializer, 
    ReservationCreateSerializer, 
    ReservationListSerializer
)

Reservation = get_model('helpdesk', 'Reservation')
ReservationItem = get_model('helpdesk', 'ReservationItem')
Assign = get_model('helpdesk', 'Assign')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ReservationApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsClientOnly,)
    permission_action = {
        'destroy': [IsReservationOwnerOrReject,],
        'partial_update': [IsReservationOwnerOrReject,]
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
        self.assign_status = None
        self.rsv_item_status = PUSH

        return super().initialize_request(request, *args, **kwargs)

    @property
    def queryset(self):
        rsv_item_prefetch = None

        if self.assign_status is not None:
            q = Q(assign__status=self.assign_status) & Q(status=PUSH)

            if self.rsv_item_status == PULL:
                q = Q(status=self.rsv_item_status)

            rsv_item_prefetch = ReservationItem.objects \
                .prefetch_related(Prefetch('assign'), Prefetch('schedule'),
                                  Prefetch('segment'), Prefetch('sla'), 
                                  Prefetch('priority'), Prefetch('issue')) \
                .select_related('assign', 'schedule', 'segment', 'sla', 'priority',
                                'issue') \
                .filter(q)

        q = Reservation.objects \
            .prefetch_related(Prefetch('client'), Prefetch('consultant'),
                              Prefetch('reservation_item', queryset=rsv_item_prefetch),
                              Prefetch('reservation_item__assign')) \
            .select_related('client', 'consultant')

        return q

    def get_objects(self):
        try:
            queryset = self.queryset.filter(client__uuid=self.user.uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        
        return queryset.filter_assign(assign_status=self.assign_status,
                                      rsv_item_status=self.rsv_item_status)

    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise NotAcceptable(detail=str(e))
        
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        self.assign_status = request.query_params.get('assign_status', WAITING)
        self.rsv_item_status = request.query_params.get('rsv_item_status', PUSH)

        queryset = self.get_objects()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ReservationListSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None):
        context = {'request': request, 'uuid': uuid}
        queryset = self.get_object(uuid=uuid)
        serializer = ReservationRetrieveSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ReservationCreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = ReservationCreateSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)


class ReservationItemAPIView(viewsets.ViewSet):
    """
    POST
    ------------------

    Format;

        {
            "reservation": "uuid v4",
            "datetime": "UTC datetime"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsClientOnly,)
    permission_action = {
        'destroy': [IsReservationItemOwnerOrReject],
        'partial_update': [IsReservationItemOwnerOrReject,]
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
        q = ReservationItem.objects \
            .prefetch_related(Prefetch('reservation'), Prefetch('reservation__issue'),
                              Prefetch('reservation__sla'), Prefetch('reservation__priority'),
                              Prefetch('assign')) \
            .select_related('reservation')

        return q

    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        reservation_uuid = request.query_params.get('reservation_uuid', None)

        if reservation_uuid is not None:
            # Filter related to reservation
            try:
                queryset = self.queryset.filter(reservation__uuid=reservation_uuid)
            except (ValidationError, ObjectDoesNotExist) as e:
                raise NotAcceptable(detail=str(e))
        else:
            queryset = self.queryset
    
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ReservationItemListSerializer(queryset_paginator, many=True,
                                                   context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ReservationItemCreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, uuid=None):
        context = {'request': request, 'uuid': uuid}
        queryset = self.get_object(uuid=uuid)
        serializer = ReservationItemRetrieveSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = ReservationItemCreateSerializer(queryset, data=request.data, partial=True,
                                                     context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)

    @method_decorator(never_cache)
    @transaction.atomic
    def put(self, request, format=None):
        context = {'request': request}
        update_fields = ['reservation'] # related field to select_related in queryset
        update_uuids = [item.get('uuid') for item in request.data]

        # Collect fields affect for updated
        for item in request.data:
            update_fields.extend(list(item.keys()))
        update_fields = list(dict.fromkeys(update_fields))
    
        queryset = self.queryset.filter(uuid__in=update_uuids).only(*update_fields)
        serializer = ReservationItemCreateSerializer(queryset, data=request.data, many=True,
                                                     context=context, fields_used=update_fields)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
