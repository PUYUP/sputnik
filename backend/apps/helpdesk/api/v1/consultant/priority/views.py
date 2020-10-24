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
from apps.helpdesk.api.v1.consultant.priority.serializers import PrioritySerializer
from apps.helpdesk.utils.permissions import IsConsultantOnly

Priority = get_model('helpdesk', 'Priority')


class PriorityApiView(viewsets.ViewSet):
    """
    GET
    ---------------

    Format;

        {
            "sla": "cc04836e-29dc-47a4-87ab-a7c212a47763"
        }

    POST
    ---------------

    Format;

        {
            "sla": "cc04836e-29dc-47a4-87ab-a7c212a47763",
            "label": "Sedang",
            "summary": "",
            "cost": 750,
            "is_active": true
        }

    PATCH
    ---------------

    Format;

        {
            "label": "Sedang",
            "summary": "",
            "cost": 750,
            "is_active": true
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def get_object(self, uuid=None, is_update=False):
        queryset = Priority.objects \
            .prefetch_related(Prefetch('user'), Prefetch('sla')) \
            .select_related('user', 'sla')

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = queryset.get(uuid=uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def get_objects(self, sla_uuid=None):
        user = self.request.user
        queryset = Priority.objects

        # If current user not creator show only PUBLISH status
        try:
            queryset = queryset.prefetch_related(Prefetch('user'), Prefetch('sla')) \
                .select_related('sla', 'user') \
                .filter(user__uuid=user.uuid, sla__uuid=sla_uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        query_params = request.query_params
        sla_uuid = query_params.get('sla_uuid')

        queryset = self.get_objects(sla_uuid=sla_uuid)
        serializer = PrioritySerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = PrioritySerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    @method_decorator(never_cache)
    def create(self, request, format=None):
        context = {'request': request}
        serializer = PrioritySerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    @method_decorator(never_cache)
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)
        serializer = PrioritySerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
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
