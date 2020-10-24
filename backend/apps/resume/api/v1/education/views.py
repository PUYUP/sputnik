from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model
from .serializers import EducationSerializer
from apps.resume.utils.permissions import IsEducationCreator
from apps.resume.utils.constants import PUBLISH

Education = get_model('resume', 'Education')


class EducationApiView(viewsets.ViewSet):
    """
    GET
    ---------------------

    Params:

        {
            "user_uuid": "UUID v4"
        }
    
    Example:
        api/v1/resume/educations/?user_uuid=a38704d0-dcc1-40b8-950f-2c2ef941d3d6


    POST / PATCH
    ---------------------

    Params:

        {
            "school": "string", [required]
            "degree": "string",
            "study": "string",
            "start_year": "string",
            "end_year": "string",
            "grade": "string",
            "description": "string"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'create': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsEducationCreator],
        'destroy': [IsAuthenticated, IsEducationCreator],
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
        self.uuid = kwargs.get('uuid', None)
        self.user = request.user
        self.user_uuid = request.GET.get('user_uuid', None)

        if not self.user_uuid:
            if self.user.is_authenticated:
                self.user_uuid = self.user.uuid

        return super().initialize_request(request, *args, **kwargs)

    # Get a objects
    def get_object(self, is_update=False):
        # start query
        queryset = Education.objects

        try:
            if is_update:
                queryset = queryset.select_for_update().get(uuid=self.uuid)
            else:
                queryset = queryset.get(uuid=self.uuid)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise NotAcceptable(detail=repr(e))
        return queryset

    def get_objects(self):
        queryset = Education.objects

        # If current user not creator show only PUBLISH status
        try:
            queryset = queryset.prefetch_related(Prefetch('user')) \
                .select_related('user') \
                .filter(user__uuid=self.user_uuid) \
                .exclude(~Q(user__uuid=self.user.uuid) & ~Q(status=PUBLISH)) \
                .order_by('sort_order')
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=repr(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        queryset = self.get_objects()
        serializer = EducationSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object()
        serializer = EducationSerializer(queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = EducationSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                return Response({'detail': repr(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_object(is_update=True)

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = EducationSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        # single object
        queryset = self.get_object()

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
                    obj = Education.objects.get(user_id=self.user.id, uuid=uuid)
                    setattr(obj, 'sort_order', i + 1) # auto set with sort index

                    update_objs.append(obj)
                except (ValidationError, ObjectDoesNotExist) as e:
                    pass

            if not update_objs:
                raise NotAcceptable()

            if update_objs:
                try:
                    Education.objects.bulk_update(update_objs, ['sort_order'])
                except IntegrityError:
                    return Response({'detail': _(u"Fatal error")},
                                    status=response_status.HTTP_406_NOT_ACCEPTABLE)

                return Response({'detail': _(u"Update success")},
                                status=response_status.HTTP_200_OK)
