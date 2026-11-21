from rest_framework import serializers
from apps.api.models import Log

class LogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Log
        fields = [
            "id",
            "user",
            "user_email",
            "created_at",
            "action",
            "feature_name"
        ]

    def get_user(self, obj):
        if obj.user:
            return obj.user.profile_set.first().name
        return None

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.profile_set.first().email
        return None