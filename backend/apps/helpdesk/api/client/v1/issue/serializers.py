from rest_framework import serializers

from utils.generals import get_model
from utils.mixin.api import DynamicFieldsModelSerializer

Issue = get_model('helpdesk', 'Issue')
Topic = get_model('master', 'Topic')


class IssueSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='helpdesk_api:client:issue-detail',
                                               lookup_field='uuid', read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    topic = serializers.SlugRelatedField(many=True, slug_field='uuid', queryset=Topic.objects.all())

    # display purpose only
    topic_label = serializers.SlugRelatedField(many=True, read_only=True, slug_field='label',
                                               source='topic')
    permalink = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Issue
        fields = '__all__'

    def get_permalink(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.permalink)
