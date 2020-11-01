from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import Prefetch
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

from rest_framework import viewsets, status as response_status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.generals import get_model
from apps.helpdesk.api.v1.consultant.priority.serializers import PrioritySerializer
from apps.helpdesk.utils.permissions import IsConsultantOnly, IsObjectOwnerOrReject, IsResumeCompleteOrReject

Priority = get_model('helpdesk', 'Priority')


class PriorityApiView(viewsets.ViewSet):
    """
    GET
    ---------------

    Format;

        {
            "sla_uuid": "cc04836e-29dc-47a4-87ab-a7c212a47763"
        }

    POST
    ---------------

    Format;

        {
            "sla": "cc04836e-29dc-47a4-87ab-a7c212a47763",
            "label": "Sedang",
            "description": "",
            "cost": 750,
            "is_active": true
        }

    PATCH
    ---------------

    Format;

        {
            "label": "Sedang",
            "description": "",
            "cost": 750,
            "is_active": true
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly, IsResumeCompleteOrReject)
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
        queryset = Priority.objects \
            .prefetch_related(Prefetch('user'), Prefetch('sla')) \
            .select_related('sla', 'user') \
            .filter(user__uuid=self.user.uuid)
        return queryset

    # single object
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    # multiple objects
    def get_objects(self, sla_uuid=None):
        try:
            queryset = self.queryset.filter(sla__uuid=sla_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        sla_uuid = request.query_params.get('sla_uuid', None)
        if not sla_uuid:
            raise NotAcceptable(detail=_("Param sla_uuid required!"))

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
        serializer = PrioritySerializer(data=request.data, many=True, context=context)
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

        serializer = PrioritySerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_403_FORBIDDEN)

    @method_decorator(never_cache)
    @transaction.atomic
    def put(self, request, format=None):
        context = {'request': request}
        update_fields = list()
        update_uuids = [item.get('uuid', None) for item in request.data]

        # Collect fields affect for updated
        for item in request.data:
            update_fields.extend(list(item.keys()))
        update_fields = list(dict.fromkeys(update_fields))

        queryset = self.queryset.filter(uuid__in=update_uuids).only(*update_fields)
        serializer = PrioritySerializer(queryset, data=request.data, many=True, context=context,
                                        fields_used=update_fields)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @method_decorator(never_cache)
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid=uuid)

        self.check_object_permissions(request, queryset)
    
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)

    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['DELETE'], detail=False, permission_classes=[IsAuthenticated],
            url_path='delete', url_name='delete')
    def delete(self, request, format=None):
        uuids = [item.get('uuid', None) for item in request.data]

        try:
            queryset = self.queryset.filter(uuid__in=uuids, rule__user__uuid=request.user.uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))

        if queryset.exists():
            queryset.delete()
            return Response(status=response_status.HTTP_204_NO_CONTENT)
        raise NotFound()
