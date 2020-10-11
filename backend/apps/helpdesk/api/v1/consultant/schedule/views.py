from django.db.models.query import QuerySet
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.http import request
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
from .serializers import ScheduleSerializer

Schedule = get_model('helpdesk', 'Schedule')


class ScheduleApiView(viewsets.ViewSet):
    """
    POST
    ------------------
        {
            "schedule_expertises": [
                {"expertise": '7905433c-966f-4f3a-b1da-66e88c83ecc0'},
                {"expertise": '7905433c-966f-4f3a-b1da-66e88c83ecc1'},
            ],
            "label": "string",
            "dtstart": "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]",
            "dtuntil": "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]",
            "wkst": "string"
        }
    
    Example:

        {
            "schedule_expertises": [
                {"expertise": "7905433c-966f-4f3a-b1da-66e88c83ecc0"}
            ],
            "label": "Jadwal 1",
            "dtstart": "2020-10-09T00:04:29+07:00",
            "dtuntil": "2020-10-19T00:04:29+07:00",
            "wkst": "SU"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated, IsConsultantOnly],
        'create': [IsAuthenticated, IsConsultantOnly],
        'retrieve': [IsAuthenticated, IsConsultantOnly],
        'partial_update': [IsAuthenticated, IsConsultantOnly],
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

    # Single object
    def get_object(self, uuid=None, is_update=False):
        queryset = Schedule.objects

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

    def list(self, request, format=None):
        context = {'request': request}
        user_uuid = request.query_params.get('user_uuid') # :user uuid

        queryset = Schedule.objects \
            .prefetch_related(Prefetch('user'), Prefetch('schedule_expertises'),
                              Prefetch('schedule_expertises__expertise')) \
            .select_related('user') \
            .order_by('sort_order')

        # check permission
        self.check_permissions(request)

        # access as public only show active schedules
        if (user_uuid):
            queryset = queryset.filter(user__uuid=user_uuid) \
                .exclude(~Q(user__uuid=request.user.uuid) & ~Q(is_active=True))
        else:
            queryset = queryset.filter(user_id=request.user.id)

        serializer = ScheduleSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}

        serializer = ScheduleSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            except IntegrityError as e:
                return Response({'detail': repr(e)},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, uuid=None):
        context = {'request': request}
    
        queryset = self.get_object(uuid=uuid)
        serializer = ScheduleSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_object(uuid=uuid, is_update=True)

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = ScheduleSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

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

    """***********
    BULK UPDATES
    ***********"""
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['patch'], detail=False,
            permission_classes=[IsAuthenticated, IsConsultantOnly],
            url_path='bulk-updates', url_name='view_bulk_updates')
    def view_bulk_updates(self, request, uuid=None):
        """
        Params:
            [
                {"uuid": "adadafa"},
                {"uuid": "adadafa"}
            ]
        """
        context = {'request': request}
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
