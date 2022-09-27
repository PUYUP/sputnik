from django.db import models
from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import DynamicFieldsModelSerializer
from apps.person.api.profile.v1.serializers import ProfileSerializer
from ....consultant.v1.priority.serializers import PrioritySerializer
from ....consultant.v1.sla.serializers import SLASerializer
from ....consultant.v1.segment.serializers import SegmentSerializer
from ....client.v1.issue.serializers import IssueSerializer


Reservation = get_model('helpdesk', 'Reservation')
ReservationItem = get_model('helpdesk', 'ReservationItem')


""" RESERVATION ITEM """
class ReservationItemSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    reservation = serializers.SlugRelatedField(slug_field='uuid', queryset=Reservation.objects.all())
    assign_status = serializers.CharField(read_only=True)
    assign_uuid = serializers.UUIDField(read_only=True, source='assign.uuid')
    payment_status = serializers.CharField(read_only=True, source='assign.assigned.invoice.status')
    issue_label = serializers.CharField(read_only=True)
    total_cost = serializers.IntegerField(read_only=True)

    class Meta:
        model = ReservationItem
        fields = '__all__'


""" RETRIEVE: RESERVATION """
class ReservationRetrieveSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:reservation-detail',
                                               lookup_field='uuid', read_only=True)
    issue = IssueSerializer(read_only=True, fields_used=('uuid', 'label', 'topic_label', 'description',))
    client = ProfileSerializer(read_only=True, source='client.profile')
    segment = SegmentSerializer(read_only=True, fields_used=('uuid', 'canal', 'canal_label', 'quota',
                                                             'open_hour', 'open_hour_formated',
                                                             'close_hour', 'close_hour_formated',))
    sla = SLASerializer(read_only=True, fields_used=('uuid', 'label_verbose', 'description', 'promise',
                                                     'grace_periode', 'cost', 'allocation',))
    priority = PrioritySerializer(read_only=True)
    reservation_item = ReservationItemSerializer(many=True, read_only=True)
    total_cost = serializers.IntegerField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink_for_consultant)


""" LIST: RESERVATION """
class ReservationListSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:reservation-detail',
                                               lookup_field='uuid', read_only=True)
    issue_label = serializers.CharField(read_only=True, source='issue.label')
    total_cost = serializers.IntegerField(read_only=True)
    permalink = serializers.SerializerMethodField(read_only=True)
    reservation_item = ReservationItemSerializer(many=True, read_only=True,
                                                 fields_used=('uuid', 'datetime', 'status',
                                                              'assign_status', 'assign_uuid', 
                                                              'number', 'payment_status',))

    class Meta:
        model = Reservation
        fields = ('uuid', 'url', 'issue_label', 'total_cost', 'permalink', 'reservation_item',)

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink_for_consultant)
