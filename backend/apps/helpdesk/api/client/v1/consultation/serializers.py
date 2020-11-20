from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.validators import CleanValidateMixin
from utils.mixin.api import (
    DynamicFieldsModelSerializer, 
    ListSerializerUpdateMappingField, 
    WritetableFieldPutMethod
)
from ..issue.serializers import IssueSerializer
from ....consultant.v1.priority.serializers import PrioritySerializer
from ....consultant.v1.sla.serializers import SLASerializer
from ....consultant.v1.segment.serializers import SegmentSerializer

from apps.person.api.profile.v1.serializers import ProfileSerializer

Reservation = get_model('helpdesk', 'Reservation')
ReservationItem = get_model('helpdesk', 'ReservationItem')
Issue = get_model('helpdesk', 'Issue')
Priority = get_model('helpdesk', 'Priority')
Schedule = get_model('helpdesk', 'Schedule')
Segment = get_model('helpdesk', 'Segment')
SLA = get_model('helpdesk', 'SLA')
User = get_model('person', 'User')


class ReservationItemCreateListSerializer(ListSerializerUpdateMappingField, serializers.ListSerializer):
    pass


""" RESERVATION ITEM: CREATE/UPDATE """
class ReservationItemCreateSerializer(DynamicFieldsModelSerializer, CleanValidateMixin,
                                      WritetableFieldPutMethod, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:client:reservation_item-detail',
                                               lookup_field='uuid', read_only=True)

    reservation = serializers.SlugRelatedField(slug_field='uuid', queryset=Reservation.objects.all())
    issue = serializers.SlugRelatedField(slug_field='uuid', queryset=Issue.objects.all())
    schedule = serializers.SlugRelatedField(slug_field='uuid', queryset=Schedule.objects.all())
    segment = serializers.SlugRelatedField(slug_field='uuid', queryset=Segment.objects.all())
    sla = serializers.SlugRelatedField(slug_field='uuid', queryset=SLA.objects.all())
    priority = serializers.SlugRelatedField(slug_field='uuid', queryset=Priority.objects.all())

    class Meta:
        model = ReservationItem
        list_serializer_class = ReservationItemCreateListSerializer
        fields = '__all__'


""" RESERVATION ITEM: RETRIEVE """
class ReservationItemRetrieveSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    issue = IssueSerializer(read_only=True, fields_used=('uuid', 'label', 'topic_label', 'description',))
    consultant = ProfileSerializer(read_only=True, source='consultant.profile')
    segment = SegmentSerializer(read_only=True, fields_used=('uuid', 'canal', 'canal_label', 'quota',
                                                             'open_hour', 'open_hour_formated',
                                                             'close_hour', 'close_hour_formated',))
    sla = SLASerializer(read_only=True, fields_used=('uuid', 'label_verbose', 'description', 'promise',
                                                     'grace_periode', 'cost', 'allocation',))
    priority = PrioritySerializer(read_only=True)

    class Meta:
        model = ReservationItem
        fields = '__all__'


""" RESERVATION ITEM: LIST """
class ReservationItemListSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    assign_status = serializers.CharField(read_only=True)
    issue_label = serializers.CharField(read_only=True, source='issue.label')

    class Meta:
        model = ReservationItem
        fields = '__all__'


""" CREATE / UPDATE: RESERVATION """
class ReservationCreateSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:client:reservation-detail',
                                               lookup_field='uuid', read_only=True)
    client = serializers.HiddenField(default=serializers.CurrentUserDefault())
    consultant = serializers.SlugRelatedField(slug_field='uuid', queryset=User.objects.all())

    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink_for_client)


""" RETRIEVE: RESERVATION """
class ReservationRetrieveSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:client:reservation-detail',
                                               lookup_field='uuid', read_only=True)
    reservation_item = ReservationItemRetrieveSerializer(many=True, read_only=True)
    total_cost = serializers.IntegerField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink_for_client)


""" LIST: RESERVATION """
class ReservationListSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:client:reservation-detail',
                                               lookup_field='uuid', read_only=True)
    consultant = serializers.CharField(read_only=True, source='consultant.first_name')
    total_cost = serializers.IntegerField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)
    reservation_item = ReservationItemListSerializer(many=True, read_only=True,
                                                     fields_used=('uuid', 'datetime', 'status',
                                                                  'issue_label', 'assign_status', 
                                                                  'number',))

    class Meta:
        model = Reservation
        fields = ('uuid', 'url', 'total_cost', 'permalink',
                  'reservation_item', 'consultant',)

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink_for_client)
