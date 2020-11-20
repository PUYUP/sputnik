from rest_framework import serializers

from utils.generals import get_model

Assign = get_model('helpdesk', 'Assign')


class AssignSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:consultant:assign-detail',
                                               lookup_field='uuid', read_only=True)

    class Meta:
        model = Assign
        fields = '__all__'
