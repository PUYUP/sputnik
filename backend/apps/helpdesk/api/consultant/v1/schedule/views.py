from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination

from apps.helpdesk.utils.permissions import (
    IsConsultantOnly, 
    IsObjectOwnerOrReject, IsResumeCompleteOrReject, 
    IsScheduleTermOwnerOrReject
)
from utils.generals import get_model
from utils.pagination import build_result_pagination
from apps.helpdesk.utils.constants import ONCE
from .serializers import (
    ScheduleExpertiseSerializer, 
    ScheduleSerializer, 
    ScheduleTermSerializer
)

Schedule = get_model('helpdesk', 'Schedule')
ScheduleTerm = get_model('helpdesk', 'ScheduleTerm')
Rule = get_model('helpdesk', 'Rule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class ScheduleApiView(viewsets.ViewSet):
    """
    POST
    ------------------

    Format;

        {
            "label": "string",
            "is_active": "boolean"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'create': [IsConsultantOnly, IsResumeCompleteOrReject,],
        'put': [IsConsultantOnly, IsResumeCompleteOrReject,],
        'destroy': [IsConsultantOnly, IsObjectOwnerOrReject, IsResumeCompleteOrReject,],
        'partial_update': [IsConsultantOnly, IsObjectOwnerOrReject, IsResumeCompleteOrReject,]
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
        q = Schedule.objects.prefetch_related(
            Prefetch('user'),
            Prefetch('schedule_expertise__expertise'),
            Prefetch('schedule_expertise__expertise__topic'),
            Prefetch('schedule_term__rule'),
            Prefetch('schedule_term__rule__rule_value'),
            Prefetch('segment__sla'),
            Prefetch('segment__sla__priority')) \
        .select_related('schedule_term', 'user') \
        .exclude(~Q(user__uuid=self.user.uuid) & Q(is_active=False) |
                 ~Q(user__uuid=self.user.uuid) & Q(schedule_term__dtstart__lte=timezone.now())
                 & Q(schedule_term__direction=ONCE) |
                 ~Q(user__uuid=self.user.uuid) & ~Q(segment__isnull=False))

        return q

    @property
    def queryset_list(self):
        q = Schedule.objects.prefetch_related(
            Prefetch('schedule_expertise'),
            Prefetch('schedule_expertise__expertise'),
            Prefetch('schedule_expertise__expertise__topic'),
            Prefetch('segment'),
            Prefetch('schedule_term'),
            Prefetch('schedule_term__rule'),
            Prefetch('schedule_term__rule__rule_value')) \
        .select_related('schedule_term') \
        .exclude(~Q(user__uuid=self.user.uuid) & Q(is_active=False) |
                 ~Q(user__uuid=self.user.uuid) & Q(schedule_term__dtstart__lte=timezone.now())
                 & Q(schedule_term__direction=ONCE) |
                 ~Q(user__uuid=self.user.uuid) & ~Q(segment__isnull=False))

        return q

    """ SCHEDULE: OBJECT """
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise NotAcceptable(detail=str(e))

        return queryset

    """ SCHEDULE: LIST """
    def list(self, request, format=None):
        context = {'request': request}

        # if user_uuid not set, user current user.uuid
        user_uuid = request.query_params.get('user_uuid', None)
        if user_uuid is None:
            user_uuid = self.user.uuid

        queryset = self.queryset_list.filter(user__uuid=user_uuid).order_by('sort_order')
        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ScheduleSerializer(queryset_paginator, many=True, context=context,
                                        fields_used=('url', 'uuid', 'label', 'expertise',
                                                     'is_active', 'permalink', 'permalink_schedule_reservation', 
                                                     'segment_label', 'schedule_term',))
        pagination_result = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(pagination_result, status=response_status.HTTP_200_OK)

    """ SCHEDULE: CREATE """
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ScheduleSerializer(data=request.data, context=context,
                                        fields_used=('user', 'uuid', 'label', 'is_active',
                                                     'description', 'permalink',))
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ SCHEDULE: GET """
    def retrieve(self, request, uuid=None):
        context = {'request': request, 'uuid': uuid}
        queryset = self.get_object(uuid=uuid)
        serializer = ScheduleSerializer(queryset, many=False, context=context,
                                        fields_used=('schedule_expertise', 'uuid', 'label', 'is_active',
                                                     'create_date', 'schedule_term', 'segment', 
                                                     'description', 'user', 'consultant',))
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """ SCHEDULE: UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = ScheduleSerializer(queryset, data=request.data, partial=True, context=context,
                                        fields_used=('uuid', 'label', 'is_active', 'description',))
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ SCHEDULE: DESTROY """
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
        update_fields = ['user'] # related field to select_related in queryset
        update_uuids = [item.get('uuid') for item in request.data]

        # Collect fields affect for updated
        for item in request.data:
            update_fields.extend(list(item.keys()))
        update_fields = list(dict.fromkeys(update_fields))
    
        queryset = self.queryset_list.filter(uuid__in=update_uuids).only(*update_fields)
        serializer = ScheduleSerializer(queryset, data=request.data, many=True, context=context,
                                        fields_used=update_fields)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)


""" TERMS """
class ScheduleTermApiView(viewsets.ViewSet):
    """
    GET
    ------------

    Format;

        {
            "schedule_uuid": "uuid v4"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly, IsResumeCompleteOrReject,)
    permission_action = {
        'partial_update': [IsAuthenticated, IsScheduleTermOwnerOrReject],
        'destroy': [IsAuthenticated, IsScheduleTermOwnerOrReject],
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
        q = ScheduleTerm.objects.prefetch_related(Prefetch('schedule')) \
            .select_related('schedule')
        return q

    # single object
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
        schedule_uuid = request.query_params.get('schedule_uuid', None)
        if schedule_uuid is None:
            raise NotAcceptable(detail=_("Param schedule_uuid required!"))
        
        try:
            queryset = self.queryset.filter(schedule__uuid=schedule_uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))

        serializer = ScheduleTermSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ScheduleTermSerializer(data=request.data, context=context)
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
        serializer = ScheduleTermSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = ScheduleTermSerializer(queryset, data=request.data, partial=True,
                                            context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)


""" EXPERTISES """
class ScheduleExpertiseApiView(viewsets.ViewSet):
    """
    GET
    ------------

    Params;

        {
            "schedule_uuid": "abcf-afaa"
        }

    POST / PATCH
    -----------

    Params;

        {
            "schedule": "85eab55d-9466-4029-8725-10405d5594cd",
            "expertise": "1182676b-29e7-4bca-8dfd-b3596cd61da9"
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
        q = ScheduleExpertise.objects \
            .prefetch_related(Prefetch('schedule'), Prefetch('expertise'),
                              Prefetch('expertise__topic')) \
            .select_related('schedule', 'expertise')
        return q

    # single object
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update() \
                    .get(uuid=uuid, user__uuid=self.user.uuid)
            else:
                queryset = self.queryset.get(uuid=uuid, user__uuid=self.user.uuid)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    # multiple objects
    def get_objects(self, schedule_uuid=None):
        try:
            queryset = self.queryset.filter(schedule__uuid=schedule_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        schedule_uuid = request.query_params.get('schedule_uuid', None)
        if not schedule_uuid:
            raise NotAcceptable(detail=_("Param schedule_uuid required"))

        queryset = self.get_objects(schedule_uuid=schedule_uuid)
        serializer = ScheduleExpertiseSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
        serializer = ScheduleExpertiseSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ScheduleExpertiseSerializer(data=request.data, many=True, context=context)
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
    
        serializer = ScheduleExpertiseSerializer(queryset, data=request.data, partial=True,
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
    
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)

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
        serializer = ScheduleExpertiseSerializer(queryset, data=request.data, many=True, context=context,
                                                 fields_used=update_fields)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['delete'], detail=False, permission_classes=[IsAuthenticated],
            url_path='delete', url_name='delete')
    def delete(self, request, format=None):
        uuids = [item.get('uuid', None) for item in request.data]

        try:
            queryset = self.queryset.filter(uuid__in=uuids, user__uuid=request.user.uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))

        if queryset.exists():
            queryset.delete()
            return Response(status=response_status.HTTP_204_NO_CONTENT)
        raise NotFound()
