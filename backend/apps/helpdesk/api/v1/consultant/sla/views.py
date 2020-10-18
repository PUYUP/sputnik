from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import Prefetch
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from utils.generals import get_model
from apps.helpdesk.api.v1.consultant.sla.serializers import SLASerializer
from apps.helpdesk.utils.permissions import IsConsultantOnly

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
            "summary": null,
            "promise": "saa",
            "secret_content": null,
            "grace_periode": 10,
            "cost": 10000,
            "is_active": true
        }

    PATCH
    ---------------

    Format;

        {
            "label": "abc",
            "summary": null,
            "promise": "saa",
            "secret_content": null,
            "grace_periode": 10,
            "cost": 10000,
            "is_active": true
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def get_object(self, uuid=None, is_update=False):
        queryset = SLA.objects \
            .prefetch_related(Prefetch('user'), Prefetch('segment'), Prefetch('schedule')) \
            .select_related('user', 'segment', 'schedule')

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = queryset.get(uuid=uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def get_objects(self, segment_uuid=None):
        user = self.request.user
        queryset = SLA.objects

        # If current user not creator show only PUBLISH status
        try:
            queryset = queryset.prefetch_related(Prefetch('schedule'), Prefetch('priorities'),
                                                 Prefetch('user'), Prefetch('segment')) \
                .select_related('schedule', 'segment', 'user') \
                .filter(user__uuid=user.uuid, segment__uuid=segment_uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        query_params = request.query_params
        segment_uuid = query_params.get('segment_uuid')

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
        serializer = SLASerializer(queryset, data=request.data, partial=True, context=context)
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
