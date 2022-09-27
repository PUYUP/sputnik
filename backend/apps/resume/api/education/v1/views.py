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
from apps.resume.utils.permissions import IsObjectOwnerOrReject
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
        q = Education.objects.prefetch_related(Prefetch('user')) \
            .select_related('user')
        return q

    # single objects
    def get_object(self, uuid=None, is_update=False):
        try:
            if is_update:
                queryset = self.queryset.select_for_update().get(uuid=uuid)
            else:
                queryset = self.queryset.get(uuid=uuid)
        except (ValidationError, ObjectDoesNotExist) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    # multiple objects
    def get_objects(self, user_uuid=None):
        try:
            queryset = self.queryset.filter(user__uuid=user_uuid) \
                .exclude(~Q(user__uuid=self.user.uuid) & ~Q(status=PUBLISH)) \
                .order_by('sort_order')
        except (ValidationError, Exception) as e:
            raise NotAcceptable(detail=str(e))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        user_uuid = request.query_params.get('user_uuid', None)
        if user_uuid is None:
            user_uuid = self.user.uuid

        queryset = self.get_objects(user_uuid=user_uuid)
        serializer = EducationSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)
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
                return Response({'detail': str(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid, is_update=True)

        self.check_object_permissions(request, queryset)

        serializer = EducationSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

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
        
        queryset = self.queryset.filter(uuid__in=update_uuids).only(*update_fields)
        serializer = EducationSerializer(queryset, data=request.data, many=True, context=context,
                                         fields_used=update_fields)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
