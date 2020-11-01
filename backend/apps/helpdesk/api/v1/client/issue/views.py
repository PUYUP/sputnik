from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models.query import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from utils.generals import get_model
from utils.pagination import build_result_pagination
from apps.helpdesk.api.v1.client.issue.serializers import IssueSerializer

Issue = get_model('helpdesk', 'Issue')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class IssueAPIView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def initialize_request(self, request, *args, **kwargs):
        self.user = request.user
        return super().initialize_request(request, *args, **kwargs)

    @property
    def queryset(self):
        q = Issue.objects.prefetch_related(Prefetch('topic'), Prefetch('user')) \
            .select_related('user')
        return q

    def get_objects(self):
        try:
            queryset = self.queryset.filter(user__uuid=self.user.uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

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
        queryset = self.get_objects()
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = IssueSerializer(queryset_paginator, many=True, context=context,
                                     fields_used=('uuid', 'label', 'number', 'topic',
                                                  'topic_label', 'url', 'permalink',))
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = IssueSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = IssueSerializer(data=request.data, context=context)
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

        serializer = IssueSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
