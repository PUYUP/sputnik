from apps.helpdesk.models.models import RuleValue
from apps.helpdesk.utils.constants import INCLUSION
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from utils.generals import get_model
from apps.helpdesk.utils.permissions import IsConsultantOnly

from .serializers import RuleSerializer

Rule = get_model('helpdesk', 'Rule')


class RuleApiView(viewsets.ViewSet):
    """
    GET
    -----------------

    Format;

        {
            "recurrence_uuid": "321fae60-305e-424f-8b66-be7867377e0e"
        }


    POST
    -----------------

    Format;

        {
            "recurrence": "321fae60-305e-424f-8b66-be7867377e0e",
            "type": "integer",
            "identifier": "byweekday",
            "rule_values": [
                {"value_integer": 10}
            ]
        }

    PATCH
    -----------------

    Format;

        {
            "type": "integer",
            "rule_values": [
                {"value_integer": 10, "uuid": "776d95a5-6c5e-4c88-9b3d-57347ec74500"}
            ]
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def list(self, request, format=None):
        context = {'request': request}
        query_params = request.query_params
        recurrence_uuid = query_params.get('recurrence_uuid', None)
        mode = query_params.get('mode', INCLUSION)

        if recurrence_uuid:
            try:
                queryset = Rule.objects \
                    .prefetch_related(Prefetch('rule_values'), Prefetch('recurrence')) \
                    .select_related('recurrence') \
                    .filter(recurrence__uuid=recurrence_uuid, mode=mode)
            except (ValidationError, Exception) as e:
                return Response({'detail': repr(e)}, status=response_status.HTTP_403_FORBIDDEN)

            serializer = RuleSerializer(queryset, many=True, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(status=response_status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        try:
            queryset = Rule.objects \
                .prefetch_related(Prefetch('rule_values'), Prefetch('recurrence')) \
                .select_related('recurrence') \
                .get(uuid=uuid)
        except (ObjectDoesNotExist, ValidationError) as e:
            raise NotAcceptable(detail=repr(e))

        serializer = RuleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = RuleSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        try:
            queryset = Rule.objects \
                .prefetch_related(Prefetch('rule_values'), Prefetch('recurrence')) \
                .select_related('recurrence') \
                .select_for_update() \
                .get(uuid=uuid)
        except (ObjectDoesNotExist, ValidationError) as e:
            raise NotAcceptable(detail=repr(e))

        serializer = RuleSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        values = request.data.get('rule_values', list())
        values_uuid = [item.get('uuid') for item in values]

        queryset = RuleValue.objects \
            .prefetch_related(Prefetch('recurrence'), Prefetch('recurrence__schedule'),
                              Prefetch('recurrence__schedule__user')) \
            .select_related('recurrence') \
            .filter(uuid__in=values_uuid, recurrence__schedule__user_id=request.user.id)

        # execute delete
        if queryset.exists():
            queryset.delete()
            return Response(
                {'detail': _("Delete success!")},
                status=response_status.HTTP_204_NO_CONTENT)
        return NotFound()
