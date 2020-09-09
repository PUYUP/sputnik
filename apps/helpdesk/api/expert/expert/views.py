import datetime

from django.conf import settings
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from rest_framework import status as response_status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable

from utils.generals import get_model

from apps.helpdesk.api.expert.expert.serializers import ExpertSerializer

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()

User = get_model('person', 'User')


class ExpertApiView(viewsets.ViewSet):
    lookup_field = 'username'
    permission_classes = (AllowAny,)

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        response = dict()
        response['count'] = _PAGINATOR.count
        response['per_page'] = settings.PAGINATION_PER_PAGE
        response['navigate'] = {
            'offset': _PAGINATOR.offset,
            'limit': _PAGINATOR.limit,
            'previous': _PAGINATOR.get_previous_link(),
            'next': _PAGINATOR.get_next_link(),
        }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        """
        Format:
            /?day=23&month=12&year=2010&expertise[]=1&expertise[]=2

        Params:
            day = integer of day number
            month = integer of month number
            year = integer of year
            expertise[] = list id of expertise, separated with comma
        """
        date_error = dict()
        context = {'request': request}
        params = request.query_params
        user = request.user

        expertise = params.getlist('expertise[]')
        day = params.get('day')
        c_day = timezone.now().day

        month = params.get('month')
        c_month = timezone.now().month

        year = params.get('year')
        c_year = timezone.now().year

        # validate date params
        if day and not day.isdigit():
            date_error['day'] = _("Day must a integer")

        if month and not month.isdigit():
            date_error['month'] = _("Month must a integer")

        if year and not year.isdigit():
            date_error['year'] = _("Year must a integer")

        if date_error:
            raise NotAcceptable(detail=date_error)

        # general query
        # Q(schedules__isnull=False), Q(schedules__is_active=True)
        queryset = User.objects \
            .filter() \
            .distinct()

        # filter by date
        if day or month or year:
            q_month = month if month else c_month
            q_year = year if year else c_year

            date_filter = [
                Q(schedules__open_date__month=q_month),
                Q(schedules__open_date__year=q_year)
            ]

            if day:
                date_filter.append(Q(schedules__open_date__day=day))
            queryset = queryset.filter(*date_filter)

        # filter by expertise
        if expertise:
            try:
                queryset = queryset.filter(schedules__expertise__in=expertise)
            except ValueError as e:
                raise NotAcceptable(detail=_("Expertise must number"))

        queryset_paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ExpertSerializer(queryset_paginator, many=True, context=context)
        return self.get_response(serializer)
