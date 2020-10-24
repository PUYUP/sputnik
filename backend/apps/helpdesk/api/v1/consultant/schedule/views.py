from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.decorators import action

from apps.helpdesk.utils.permissions import IsConsultantOnly
from utils.generals import get_model
from .serializers import RecurrenceSerializer, ScheduleExpertiseSerializer, ScheduleSerializer

Schedule = get_model('helpdesk', 'Schedule')
Recurrence = get_model('helpdesk', 'Recurrence')
Rule = get_model('helpdesk', 'Rule')
ScheduleExpertise = get_model('helpdesk', 'ScheduleExpertise')


class ScheduleApiView(viewsets.ViewSet):
    """
    POST
    ------------------

    If 'rules' type set as 'integer' then 'rules_value' list set as 'value_integer'

        {
            "schedule_expertises": [
                {"expertise": '7905433c-966f-4f3a-b1da-66e88c83ecc0'},
                {"expertise": '7905433c-966f-4f3a-b1da-66e88c83ecc1'},
            ],
            "label": "string"
        }
    
    Example:

        {
            "schedule_expertises": [
                {"expertise": "7905433c-966f-4f3a-b1da-66e88c83ecc0"}
            ],
            "label": "Jadwal 5"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated, IsConsultantOnly],
        'create': [IsAuthenticated, IsConsultantOnly],
        'retrieve': [IsAuthenticated, IsConsultantOnly],
        'partial_update': [IsAuthenticated, IsConsultantOnly]
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

    """ SCHEDULE: OBJECT """
    def get_object(self, uuid=None, is_update=False):
        queryset = Schedule.objects.prefetch_related(
            Prefetch('schedule_expertises'),
            Prefetch('schedule_expertises__expertise'),
            Prefetch('schedule_expertises__expertise__topic'),
            Prefetch('recurrence')
        ) \
        .select_related('recurrence')

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = queryset.get(uuid=uuid)
        except ValidationError as e:
            raise NotAcceptable(detail=repr(e))
        except ObjectDoesNotExist:
            raise NotFound()

        return queryset

    """ SCHEDULE: LIST """
    def list(self, request, format=None):
        context = {'request': request}
        user_uuid = request.query_params.get('user_uuid') # :user uuid

        queryset = Schedule.objects \
            .prefetch_related(Prefetch('user'), Prefetch('schedule_expertises'),
                              Prefetch('schedule_expertises__expertise'),
                              Prefetch('schedule_expertises__expertise__topic'),
                              Prefetch('recurrence'), Prefetch('segments'),
                              Prefetch('segments__user'), Prefetch('segments__slas'),
                              Prefetch('segments__slas__user')) \
            .select_related('user', 'recurrence') \
            .order_by('sort_order')

        # check permission
        self.check_permissions(request)

        # access as public only show active schedules
        if (user_uuid):
            queryset = queryset.filter(user__uuid=user_uuid) \
                .exclude(~Q(user__uuid=request.user.uuid) & ~Q(is_active=True))
        else:
            queryset = queryset.filter(user_id=request.user.id)

        serializer = ScheduleSerializer(queryset, many=True, context=context,
                                        fields=('url', 'uuid', 'label', 'expertises',))
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """ SCHEDULE: CREATE """
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}

        serializer = ScheduleSerializer(data=request.data, context=context,
                                        fields=('schedule_expertises', 'uuid', 'label', 'is_active',
                                                'user',))
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ SCHEDULE: GET """
    def retrieve(self, request, uuid=None):
        context = {'request': request, 'uuid': uuid}
        queryset = self.get_object(uuid=uuid)
        serializer = ScheduleSerializer(queryset, many=False, context=context,
                                        fields=('schedule_expertises', 'uuid', 'label', 'is_active',
                                                'create_date', 'recurrence', 'segments',))
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """ SCHEDULE: UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = ScheduleSerializer(queryset, data=request.data, partial=True, context=context,
                                        fields=('schedule_expertises', 'uuid', 'label', 'is_active',))
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ SCHEDULE: DESTROY """
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        # retrieve object
        queryset = self.get_object(uuid=uuid)

        # check permission
        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response(
            {'detail': _("Delete success!")},
            status=response_status.HTTP_204_NO_CONTENT)

    """ SCHEDULE: BULK UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['patch'], detail=False,
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='bulk-updates', url_name='bulk-updates')
    def bulk_updates(self, request, uuid=None):
        """
        Params:
            [
                {"uuid": "adadafa"},
                {"uuid": "adadafa"}
            ]
        """
        method = request.method
        user = request.user

        if not request.data:
            raise NotAcceptable()

        if method == 'PATCH':
            update_objs = list()

            for i, v in enumerate(request.data):
                uuid = v.get('uuid')
 
                try:
                    obj = Schedule.objects.get(user_id=user.id, uuid=uuid)
                    setattr(obj, 'sort_order', i + 1) # auto set with sort index

                    update_objs.append(obj)
                except (ValidationError, ObjectDoesNotExist) as e:
                    pass

            if not update_objs:
                raise NotAcceptable()

            if update_objs:
                try:
                    Schedule.objects.bulk_update(update_objs, ['sort_order'])
                except IntegrityError:
                    return Response({'detail': _(u"Fatal error")},
                                    status=response_status.HTTP_406_NOT_ACCEPTABLE)

                return Response({'detail': _(u"Update success")},
                                status=response_status.HTTP_200_OK)


"""
RECURRENCES
"""
class RecurrenceApiView(viewsets.ViewSet):
    """
    GET
    -----------

    Params;

        {
            "schedule_uuid": "b2c76dda-bcd4-44e3-92a8-9a9bbb7edad9"
        }

    POST
    -----------

    Params;

        {
            "schedule": "b2c76dda-bcd4-44e3-92a8-9a9bbb7edad9",
            "dtstart": "2020-10-13T20:22:37.489102+07:00",
            "dtuntil": "",
            "freq": 1,
            "count": 30,
            "interval": 1,
            "wkst": "MO"
        }

    PATCH
    -----------

    Params;

        {
            "dtstart": "2020-10-13T20:22:37.489102+07:00",
            "dtuntil": "",
            "freq": 1,
            "count": 30,
            "interval": 1,
            "wkst": "MO"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def initialize_request(self, request, *args, **kwargs):
        self.user = request.user
        self.schedule_uuid = request.GET.get('schedule_uuid', None)
        self.uuid = kwargs.get('uuid', None)
        return super().initialize_request(request, *args, **kwargs)

    @property
    def query(self):
        query = Recurrence.objects \
            .prefetch_related(Prefetch('schedule')) \
            .select_related('schedule')
        return query

    def get_object(self, is_update=False):
        try:
            if is_update:
                queryset = self.query.select_for_update() \
                    .get(uuid=self.uuid, schedule__user__uuid=self.user.uuid)
            else:
                queryset = self.query.get(uuid=self.uuid, schedule__user__uuid=self.user.uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def get_objects(self):
        try:
            queryset = self.query.get(schedule__uuid=self.schedule_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=repr(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        if self.schedule_uuid is None:
            raise NotAcceptable(detail=_("Param schedule_uuid required"))

        queryset = self.get_objects()
        serializer = RecurrenceSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_objects()
        serializer = RecurrenceSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = RecurrenceSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(is_update=True)
        serializer = RecurrenceSerializer(queryset, data=request.data, partial=True,
                                          context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)


"""
EXPERTISES
"""
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
    permission_classes = (IsAuthenticated, IsConsultantOnly,)

    def initialize_request(self, request, *args, **kwargs):
        self.user = request.user
        self.schedule_uuid = request.GET.get('schedule_uuid', None)
        self.uuid = kwargs.get('uuid', None)
        return super().initialize_request(request, *args, **kwargs)

    @property
    def query(self):
        query = ScheduleExpertise.objects \
            .prefetch_related(Prefetch('schedule'), Prefetch('expertise'),
                              Prefetch('expertise__topic')) \
            .select_related('schedule', 'expertise')
        return query

    def get_object(self, is_update=False):
        try:
            if is_update:
                queryset = self.query.select_for_update() \
                    .get(uuid=self.uuid, schedule__user__uuid=self.user.uuid)
            else:
                queryset = self.query.get(uuid=self.uuid, schedule__user__uuid=self.user.uuid)
        except Exception as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def get_objects(self):
        try:
            queryset = self.query.filter(schedule__uuid=self.schedule_uuid)
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=repr(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        if self.schedule_uuid is None:
            raise NotAcceptable(detail=_("Param schedule_uuid required"))

        queryset = self.get_objects()
        serializer = ScheduleExpertiseSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object()
        serializer = ScheduleExpertiseSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ScheduleExpertiseSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(is_update=True)
        serializer = ScheduleExpertiseSerializer(queryset, data=request.data, partial=True,
                                                 context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object()
        queryset.delete()
        return Response({'detail': _("Delete success!")}, status=response_status.HTTP_204_NO_CONTENT)
