from django.db import transaction
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError

from rest_framework import viewsets, status as response_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import NotAcceptable
from rest_framework.response import Response

from utils.generals import get_model
from .serializers import AttachmentSerializer

Attachment = get_model('resume', 'Attachment')


class AttachmentApiView(viewsets.ViewSet):
    """
    POST
    ----------
    Params:
        {
            "label": "string", [required]
            "description": "string",
            "file": "file" [required],
            "object_uuid": "valid uuid.4"
        }

    GET
    ----------
    Params:
        {
            "object_uuid": "valid uuid.4"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    parser_classes=[MultiPartParser]

    def get_object(self, uuid=None):
        try:
            queryset = Attachment.objects.get(uuid=uuid)
        except Exception as e:
            raise NotAcceptable(detail=_(u" ".join(e.messages)))
        return queryset

    def list(self, request, format=None):
        context = {'request': request}
        object_uuid = request.query_params.get('object_uuid')
        if not object_uuid:
            raise NotAcceptable(detail=_("object_uuid required"))

        try:
            queryset = Attachment.objects \
                .prefetch_related(Prefetch('content_type'), Prefetch('content_object')) \
                .select_related('content_type', 'content_object') \
                .filter(content_object__uuid=object_uuid)
        except Exception as e:
            raise NotAcceptable(detail=_("Something wrong %s" % type(e)))

        serializer = AttachmentSerializer(queryset, many=True, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        context = {'request': request}

        serializer = AttachmentSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except Exception as e:
                return Response({'detail': str(e)}, status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        context = {'request': request}
        queryset = self.get_object(uuid=uuid)

        # check permission
        self.check_object_permissions(request, queryset)

        serializer = AttachmentSerializer(queryset, data=request.data, partial=True, context=context)
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (ValidationError, Exception) as e:
                raise NotAcceptable(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        queryset = self.get_object(uuid)

        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response({'detail': _("Delete success!")},
                        status=response_status.HTTP_204_NO_CONTENT)
