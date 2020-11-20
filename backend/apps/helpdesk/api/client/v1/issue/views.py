from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models.query import Prefetch
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
from apps.helpdesk.utils.permissions import IsClientOnly, IsObjectOwnerOrReject
from .serializers import IssueSerializer

Issue = get_model('helpdesk', 'Issue')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class IssueAPIView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsClientOnly,)
    permission_action = {
        'destroy': [IsObjectOwnerOrReject,],
        'partial_update': [IsObjectOwnerOrReject,]
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
        q = Issue.objects.prefetch_related(Prefetch('topic'), Prefetch('user')) \
            .select_related('user')
        return q

    def get_objects(self, keyword=None):
        try:
            queryset = self.queryset.filter(user__uuid=self.user.uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        
        if keyword is not None:
            if keyword:
                queryset = queryset.filter(label__icontains=keyword)
            else:
                return []
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
        keyword = request.query_params.get('keyword')
        queryset = self.get_objects(keyword=keyword)
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = IssueSerializer(queryset_paginator, many=True, context=context,
                                     fields_used=('uuid', 'label', 'url', 'topic',
                                                  'topic_label', 'permalink',))
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

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
