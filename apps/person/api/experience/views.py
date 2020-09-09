from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist, FieldError
from django.db import transaction
from django.db.models import (
    Prefetch, Case, When, Q, Value, BooleanField, CharField, Count
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, NotAcceptable
from rest_framework.parsers import MultiPartParser

from utils.generals import get_model
from apps.person.api.experience.serializers import (
    ExperienceSerializer, 
    ExperienceAttachmentSerializer
)
from apps.person.utils.permissions import (
    IsExperienceCreator,
    IsExperienceAttachmentCreator
)
from apps.person.utils.constants import PUBLISH, DRAFT

Experience = get_model('person', 'Experience')
ExperienceAttachment = get_model('person', 'ExperienceAttachment')


class ExperienceApiView(viewsets.ViewSet):
    """
    GET
    ---------------------
    Params:
        {
            "user_uuid": "UUID v4"
        }
    
    Example:
        api/person/experiences/?user_uuid=a38704d0-dcc1-40b8-950f-2c2ef941d3d6

    POST
    ---------------------
    Params:
        {
            "title": "string", [required]
            "employment": "string-slug", [required]
            "company": "string",
            "location": "string",
            "currently": "boolean", [required]
            "start_month": "string", [required]
            "start_year": "string", [required]
            "end_month": "string",
            "end_year": "string",
            "status": "string-slug", [required]
            "description": "string"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        'list': [IsAuthenticated],
        'create': [IsAuthenticated],
        'partial_update': [IsAuthenticated, IsExperienceCreator],
        'destroy': [IsAuthenticated, IsExperienceCreator],
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

    # Get a objects
    def get_object(self, user_uuid=None, uuid=None, is_update=False):
        user = self.request.user

        # start query
        queryset = Experience.objects

        # Single object
        # uuid is :experience uuid
        if uuid:
            try:
                if is_update:
                    return queryset.select_for_update().get(uuid=uuid)
                return queryset.get(uuid=uuid)
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            except ObjectDoesNotExist:
                return None

        # All objects
        # If current user not creator show only PUBLISH status
        try:
            return queryset.prefetch_related(Prefetch('user'), Prefetch('experience_attachments')) \
                .select_related('user') \
                .filter(user__uuid=user_uuid) \
                .exclude(~Q(user__uuid=user.uuid) & Q(status=DRAFT))
        except FieldError as e:
            raise NotAcceptable(detail=str(e))

    def list(self, request, format=None):
        params_missed = dict()
        context = {'request': request}
        user = request.user
        user_uuid = request.query_params.get('user_uuid') # :user uuid

        if not user_uuid and not user.is_authenticated:
            params_missed.update({'user_uuid': _("Required")})
        else:
            user_uuid = user.uuid

        # print error if params not provided
        if params_missed:
            raise NotAcceptable(detail=params_missed)

        queryset = self.get_object(user_uuid=user_uuid)
        if queryset is None:
            raise NotFound()

        serializer = ExperienceSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}
        serializer = ExperienceSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_object(uuid=uuid, is_update=True)
        if queryset is None:
            raise NotFound()

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = ExperienceSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        queryset = self.get_object(uuid=uuid)
        if queryset is None:
            raise NotFound()

        # check permission
        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response(
            {'detail': _("Delete success!")},
            status=response_status.HTTP_204_NO_CONTENT)

    """***********
    ATTACHMENT
    ***********"""
    # LIST, CREATE
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['get', 'post'], detail=True,
            permission_classes=[IsAuthenticated], parser_classes=[MultiPartParser],
            url_path='attachments', url_name='view_attachment')
    def view_attachment(self, request, uuid=None, format=None):
        """
        Params:
            {
                "title": "string", [required]
                "description": "string",
                "attach_file": "file" [required]
            }
        """
        context = {'request': request}
        method = request.method
        user = request.user

        if method == 'POST':
            try:
                experience_obj = Experience.objects.get(uuid=uuid)
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            except ObjectDoesNotExist:
                raise NotFound(_("Experience not found"))

            context['experience'] = experience_obj
            serializer = ExperienceAttachmentSerializer(data=request.data, context=context)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except ValidationError as e:
                    return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
                return Response(serializer.data, status=response_status.HTTP_200_OK)
            return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

        elif method == 'GET':
            queryset = ExperienceAttachment.objects.annotate(
                is_creator=Case(
                    When(Q(experience__user__uuid=user.uuid), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ) \
            .prefetch_related(Prefetch('experience'), Prefetch('experience__user')) \
            .select_related('experience', 'experience__user') \
            .filter(experience__uuid=uuid)

            serializer = ExperienceAttachmentSerializer(queryset, many=True, context=context)
            return Response(serializer.data, status=response_status.HTTP_200_OK)

    # UPDATE, DELETE
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['patch', 'delete'], detail=True,
            permission_classes=[IsAuthenticated, IsExperienceAttachmentCreator],
            parser_classes=[MultiPartParser],
            url_path='attachments/(?P<attachment_uuid>[^/.]+)', 
            url_name='view_attachment_update')
    def view_attachment_update(self, request, uuid=None, attachment_uuid=None):
        """
        Params:
            {
                "title": "string",
                "description": "string",
                "attach_file": "file"
            }
        """
        context = {'request': request}
        method = request.method

        try:
            queryset = ExperienceAttachment.objects.get(uuid=attachment_uuid)
        except ValidationError as e:
            return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
        except ObjectDoesNotExist:
            raise NotFound()

        # check permission
        self.check_object_permissions(request, queryset)
        
        if method == 'PATCH':
            serializer = ExperienceAttachmentSerializer(queryset, data=request.data, partial=True, context=context)
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                except ValidationError as e:
                    return Response({'detail': _(u" ".join(e.messages))}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
                return Response(serializer.data, status=response_status.HTTP_200_OK)
            return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

        elif method == 'DELETE':
            # execute delete
            queryset.delete()
            return Response(
                {'detail': _("Delete success!")},
                status=response_status.HTTP_204_NO_CONTENT)
