from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Q
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError

from utils.generals import get_model
from .serializers import ExpertiseSerializer
from ....utils.permissions import IsExpertiseCreator

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
            "skill": "valid uuid4"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (AllowAny, IsExpertiseCreator,)

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

        queryset = Expertise.objects \
            .prefetch_related(Prefetch('skill')) \
            .select_related('skill') \
            .filter(user__uuid=user_uuid)
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
            except ValidationError as e:
                return Response({'detail': _(u" ".join(e.messages))},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            except IntegrityError:
                return Response({'detail': _(u"Keahlian ini telah ditambahkan")},
                                status=response_status.HTTP_406_NOT_ACCEPTABLE)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None, format=None):
        context = {'request': request}

        # single object
        try:
            queryset = Expertise.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        # check permission
        self.check_object_permissions(request, queryset)

        # execute delete
        queryset.delete()
        return Response(
            {'detail': _("Delete success!")},
            status=response_status.HTTP_204_NO_CONTENT)