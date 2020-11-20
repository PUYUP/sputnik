from rest_framework import serializers


class CleanValidateMixin(serializers.ModelSerializer):
    def validate(self, attrs):
        instance = self.instance
        if not self.instance:
            instance = self.Meta.model(**attrs)

        instance.clean()
        return attrs
