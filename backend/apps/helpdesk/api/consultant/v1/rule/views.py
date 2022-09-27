from apps.helpdesk.models.models import RuleValue
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
from rest_framework.decorators import action

from utils.generals import get_model
from apps.helpdesk.utils.permissions import (
    IsConsultantOnly, IsObjectOwnerOrReject, IsResumeCompleteOrReject, 
    IsRuleValueOwnerOrReject
)

from .serializers import RuleSerializer, RuleValueSerializer

Rule = get_model('helpdesk', 'Rule')


class RuleApiView(viewsets.ViewSet):
    """
    GET
    -----------------

    Format;

        {
            "schedule_term_uuid": "321fae60-305e-424f-8b66-be7867377e0e",
            "mode": "inclusion/exclusion"
        }


    POST
    -----------------

    Format;

        {
            "schedule_term": "321fae60-305e-424f-8b66-be7867377e0e",
            "type": "integer",
            "identifier": "byweekday",
            "rule_value": [
                {"value_integer": 10}
            ]
        }

    PATCH
    -----------------

    Format;

        {
            "type": "integer",
            "rule_value": [
                {"value_integer": 10, "uuid": "776d95a5-6c5e-4c88-9b3d-57347ec74500"}
            ]
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly, IsResumeCompleteOrReject,)
    permission_action = {
        'partial_update': [IsAuthenticated, IsObjectOwnerOrReject],
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

    @property
    def queryset(self):
        q = Rule.objects \
            .prefetch_related(Prefetch('rule_value'), Prefetch('schedule_term')) \
            .select_related('schedule_term')
        return q

    # single object
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ObjectDoesNotExist, ValidationError) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        mode = request.query_params.get('mode')
        schedule_term_uuid = request.query_params.get('schedule_term_uuid')

        if not mode:
            raise NotAcceptable(detail=_("Param mode required!"))

        if not schedule_term_uuid:
            raise NotAcceptable(detail=_("Param schedule_term_uuid required!"))

        try:
            queryset = self.queryset.filter(schedule_term__uuid=schedule_term_uuid, mode=mode)
        except (ValidationError, Exception) as e:
            return Response({'detail': str(e)}, status=response_status.HTTP_403_FORBIDDEN)

        serializer = RuleSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
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
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = RuleSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        identifier = request.data.get('identifier')
        rule_value = request.data.get('rule_value', list())
        rule_value_uuids = [item.get('uuid') for item in rule_value]

        # peform delete RuleValue not Rule
        queryset = RuleValue.objects \
            .prefetch_related(Prefetch('rule'), Prefetch('rule__user'), Prefetch('schedule_term')) \
            .select_related('rule', 'schedule_term') \
            .filter(rule__user__uuid=request.user.uuid)

        queryset_delete = queryset.filter(uuid__in=rule_value_uuids)
        if queryset_delete.exists():
            queryset_delete.delete()

            # check again RuleValue still exist in Rule
            queryset_check = queryset.filter(rule__uuid=uuid, rule__identifier=identifier)
            if not queryset_check.exists() and rule_value_uuids:
                # if all RuleValue gone, delete the Rule to
                try:
                    rule = Rule.objects.get(uuid=uuid, identifier=identifier, user__uuid=request.user.uuid)
                    rule.delete()
                except ObjectDoesNotExist:
                    pass

            return Response({'detail': _("Delete success!")},
                            status=response_status.HTTP_204_NO_CONTENT)
        raise NotFound()


class RuleValueApiView(viewsets.ViewSet):
    """
    GET
    --------------

    Params;

        {
            "rule_uuid": "uuid v4"
        }

    POST
    --------------

    Params multiple;

        [
            {"rule": "3531eaf3-cda3-4cee-9d08-194358b7c74b", "value_varchar": "TU"},
            {"rule": "3531eaf3-cda3-4cee-9d08-194358b7c74b", "value_varchar": "SA"}
        ]
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly, IsResumeCompleteOrReject,)
    permission_action = {
        'partial_update': [IsAuthenticated, IsRuleValueOwnerOrReject],
        'destroy': [IsAuthenticated, IsRuleValueOwnerOrReject],
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

    @property
    def queryset(self):
        q = RuleValue.objects \
            .prefetch_related(Prefetch('rule'), Prefetch('rule__user')) \
            .select_related('rule')
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
    def get_objects(self, rule_uuid=None):
        try:
            queryset = self.queryset.filter(rule__uuid=rule_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        rule_uuid = request.query_params.get('rule_uuid')
        if not rule_uuid:
            raise NotAcceptable(detail=_("Param rule_uuid required!"))

        queryset = self.get_objects(rule_uuid=rule_uuid)
        serializer = RuleValueSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @transaction.atomic
    @method_decorator(never_cache)
    def create(self, request, format=None):
        context = {'request': request}
        serializer = RuleValueSerializer(data=request.data, many=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (IntegrityError, ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
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
        serializer = RuleValueSerializer(queryset, data=request.data, many=True, context=context,
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
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = RuleValueSerializer(queryset, data=request.data, partial=True, context=context)
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
