from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status as response_status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError

from utils.generals import get_model
from .serializers import ExpertiseSerializer

Expertise = get_model('resume', 'Expertise')


class ExpertiseApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Params:
        {
            "user_uuid": "UUID v4"
        }
    
    Example:
        api/v1/resume/expertises/?user_uuid=a38704d0-dcc1-40b8-950f-2c2ef941d3d6


    POST
    ---------------------
    Params:
        {
            "topic": "valid uuid4"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)

    def initialize_request(self, request, *args, **kwargs):
        self.uuid = kwargs.get('uuid', None)
        self.user = request.user
        self.user_uuid = request.GET.get('user_uuid', None)

        if not self.user_uuid:
            if self.user.is_authenticated:
                self.user_uuid = self.user.uuid

        return super().initialize_request(request, *args, **kwargs)

    def list(self, request, format=None):
        context = {'request': request}
        queryset = Expertise.objects \
            .prefetch_related(Prefetch('topic'), Prefetch('user')) \
            .select_related('topic', 'user') \
            .filter(user__uuid=self.user_uuid) \
            .order_by('sort_order')

        serializer = ExpertiseSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ExpertiseSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        try:
            queryset = Expertise.objects.get(uuid=uuid, user_id=self.user.id)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=repr(e))

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = ExpertiseSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=repr(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        # single object
        try:
            queryset = Expertise.objects.get(uuid=uuid, user_id=self.user.id)
        except (ValidationError, ObjectDoesNotExist, Exception) as e:
            raise NotAcceptable(detail=repr(e))

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
            permission_classes=[IsAuthenticated],
            url_path='bulk-updates', url_name='view_bulk_updates')
    def view_bulk_updates(self, request, uuid=None):
        """
        Params:
            [
                {"uuid": "adadafa"},
                {"uuid": "adadafa"}
            ]
        """
        method = request.method
 
        if not request.data:
            raise NotAcceptable()

        if method == 'PATCH':
            update_objs = list()

            for i, v in enumerate(request.data):
                uuid = v.get('uuid')
 
                try:
                    obj = Expertise.objects.get(user_id=self.user.id, uuid=uuid)
                    setattr(obj, 'sort_order', i + 1) # auto set with sort index

                    update_objs.append(obj)
                except (ValidationError, ObjectDoesNotExist) as e:
                    pass

            if not update_objs:
                raise NotAcceptable()

            if update_objs:
                try:
                    Expertise.objects.bulk_update(update_objs, ['sort_order'])
                except IntegrityError:
                    return Response({'detail': _(u"Fatal error")},
                                    status=response_status.HTTP_406_NOT_ACCEPTABLE)

                return Response({'detail': _(u"Update success")},
                                status=response_status.HTTP_200_OK)
