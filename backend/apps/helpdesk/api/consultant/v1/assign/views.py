from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from utils.pagination import build_result_pagination
from apps.helpdesk.utils.permissions import IsAssignOwnerOrReject, IsConsultantOnly
from .serializers import AssignSerializer

Assign = get_model('helpdesk', 'Assign')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class AssignApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)
    permission_action = {
        'partial_update': [IsAssignOwnerOrReject],
        'destroy': [IsAssignOwnerOrReject],
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
        q = Assign.objects \
            .prefetch_related(Prefetch('client'), Prefetch('consultant'), Prefetch('reservation'),
                              Prefetch('reservation_item')) \
            .select_related('client', 'consultant', 'reservation', 'reservation_item')
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
    def get_objects(self):
        try:
            queryset = self.queryset.filter(consultant__uuid=self.user.uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        queryset = self.get_objects()

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = AssignSerializer(queryset_paginator, many=True, context=context)
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = AssignSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    @method_decorator(never_cache)
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = AssignSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)
