from apps.helpdesk.models.models import Recurrence, RuleValue
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
from .serializers import RecurrenceSerializer, ScheduleSerializer

Schedule = get_model('helpdesk', 'Schedule')
Recurrence = get_model('helpdesk', 'Recurrence')
Rule = get_model('helpdesk', 'Rule')


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
    def get_schedule(self, uuid=None, is_update=False):
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
            raise NotAcceptable({'detail': repr(e)})
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
                              Prefetch('recurrence')) \
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
                return Response({'detail': repr(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ SCHEDULE: GET """
    def retrieve(self, request, uuid=None):
        context = {'request': request, 'uuid': uuid}
        queryset = self.get_schedule(uuid=uuid)
        serializer = ScheduleSerializer(queryset, many=False, context=context,
                                        fields=('schedule_expertises', 'uuid', 'label', 'is_active',
                                                'create_date', 'recurrence',))
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """ SCHEDULE: UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_schedule(uuid=uuid, is_update=True)

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
        queryset = self.get_schedule(uuid=uuid)

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

    """ RECURRENCE: GET """
    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='recurrences', url_name='recurrences')
    def recurrences(self, request, uuid=None):
        """
        POST
        -------------------

        Format;
        
            {
                "dtstart": "YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]", [required]
                "dtuntil": "YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]",
                "freq": "integer", [required, default 1]
                "count": "integer", [required, default 30]
                "interval": "integer", [required, default 1]
                "wkst": "string" [default MO]
            }

        Example;
        If value not used ignore it from param below

            {
                "dtstart": "2020-10-13T20:22:37.489102+07:00",
                "dtuntil": "",
                "freq": 1,
                "count": 30,
                "interval": 1,
                "wkst": "MO"
            }
        """
        schedule = self.get_schedule(uuid=uuid)
        context = {'request': request, 'schedule': schedule}

        serializer = RecurrenceSerializer(schedule.recurrence, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    """ RECURRENCE: CREATE """
    @method_decorator(never_cache)
    @transaction.atomic
    @recurrences.mapping.post
    def recurrences_create(self, request, uuid=None):
        if not request.data:
            raise NotAcceptable()

        schedule = self.get_schedule(uuid=uuid)
        context = {'request': request, 'schedule': schedule}

        serializer = RecurrenceSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                return Response({'detail': repr(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ RECURRENCE: UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['get', 'patch'], detail=True,
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='recurrences/(?P<recurrence_uuid>[^/.]+)', url_name='recurrences-update')
    def recurrences_update(self, request, uuid=None, recurrence_uuid=None):
        """
        Param;
    
            {
                "dtstart": "2020-10-13T20:22:37.489102+07:00",
                "dtuntil": "",
                "freq": 1,
                "count": 30,
                "interval": 1,
                "wkst": "MO"
            }
        """
        if not request.data:
            raise NotAcceptable()

        schedule = self.get_schedule(uuid=uuid)
        context = {'request': request, 'schedule': schedule}

        try:
            instance = Recurrence.objects.select_for_update() \
                .get(schedule__uuid=uuid, schedule__user__uuid=request.user.uuid,
                     uuid=recurrence_uuid)
        except (ValidationError, Exception, ObjectDoesNotExist) as e:
            raise NotAcceptable({'detail': repr(e)})

        serializer = RecurrenceSerializer(instance, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, IntegrityError) as e:
                return Response({'detail': repr(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    """ RULE: GET """
    @action(detail=True, methods=['get'],
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='recurrences/(?P<recurrence_uuid>[^/.]+)/rules', url_name='recurrences-rules')
    def rules(self, request, uuid=None, recurrence_uuid=None):
        """
        POST
        -----------------------

        Params;

            [
                {
                    "identifier": "byweekday",
                    "type": "integer",
                    "values": [
                        {"value": 2},
                        {"value": 3}
                    ]
                }
            ]
        
        PATCH
        -----------------------

        Params;

            [
                {
                    "identifier": "byweekday",
                    "type": "integer",
                    "values": [
                        {"value": 2, "uuid": "7d0981db-ff64-4df8-bcdf-7b7daecfd6ca"},
                        {"value": 3, "uuid": "69e7a5ba-5375-4f6e-8274-f7fca96e9d35"}
                    ]
                }
            ]
        """
        schedule = self.get_schedule(uuid=uuid)
        recurrence = getattr(schedule, 'recurrence', None)
        rule_values = list()

        if recurrence:
            rules = recurrence.rules \
                .prefetch_related(Prefetch('rule_values')) \
                .all()
            
            rule_values = list()
            for r in rules:
                field = 'value_%s' % r.type
                values = r.rule_values.all()
                rule_values.append(
                    {
                        'uuid': r.uuid,
                        'identifier': r.identifier,
                        'type': r.type,
                        'values': [{'uuid': str(v.uuid), 'value': getattr(v, field)} for v in values],
                    }
                )

        return Response(rule_values, status=response_status.HTTP_200_OK)

    """ RULE: CREATE """
    @method_decorator(never_cache)
    @transaction.atomic
    @rules.mapping.post
    def rules_create(self, request, uuid=None, recurrence_uuid=None):
        if not request.data:
            raise NotAcceptable()

        schedule = self.get_schedule(uuid=uuid)
        recurrence = getattr(schedule, 'recurrence', None)
        rules = request.data

        for r in rules:
            identifier = r.get('identifier')
            values = r.get('values')
            rtype = r.get('type')

            rule, _creaed = Rule.objects.get_or_create(identifier=identifier, recurrence_id=recurrence.id, type=rtype)
            if rule:
                values_set = list()

                for v in values:
                    vdict = {'value': v.get('value')}
                    values_set.append(vdict)

                try:
                    rule.save_values(values_set)
                except Exception as e:
                    raise NotAcceptable({'detail': repr(e)})
        return Response({'detail': _("Rules created")}, status=response_status.HTTP_201_CREATED)

    """ RULE: UPDATE """
    @method_decorator(never_cache)
    @transaction.atomic
    @rules.mapping.patch
    def rule_update(self, request, uuid=None, recurrence_uuid=None):
        if not request.data:
            raise NotAcceptable()

        schedule = self.get_schedule(uuid=uuid)
        recurrence = getattr(schedule, 'recurrence', None)
        rules = request.data

        for r in rules:
            identifier = r.get('identifier')
            values = r.get('values')
            rtype = r.get('type')

            rule, _creaed = Rule.objects.get_or_create(identifier=identifier, recurrence_id=recurrence.id, type=rtype)
            if rule:
                values_set = list()

                for v in values:
                    uuid = v.get('uuid')
                    vdict = {'value': v.get('value')}
                    if uuid:
                        vdict['uuid'] = uuid
                    values_set.append(vdict)

                try:
                    rule.save_values(values_set)
                except Exception as e:
                    raise NotAcceptable({'detail': repr(e)})
        return Response({'detail': _("Rules updated")}, status=response_status.HTTP_200_OK)

    """ RULE: DELETE """
    @action(detail=True, methods=['delete'],
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='recurrences/(?P<recurrence_uuid>[^/.]+)/rules/(?P<rule_value_uuid>[^/.]+)', url_name='recurrences-rules-delete')
    def rules_delete(self, request, uuid=None, recurrence_uuid=None, rule_value_uuid=None):
        """ DELETE RULE VALUE """
        try:
            queryset = RuleValue.objects.get(uuid=rule_value_uuid, recurrence__schedule__user__uuid=request.user.uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        queryset.delete()
        return Response({'detail': _("Delete success!")}, status=response_status.HTTP_204_NO_CONTENT)
