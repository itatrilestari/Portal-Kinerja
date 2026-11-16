from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.api.models import Profile

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password"
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get("username"),
            email=validated_data.get("email", ""),
            password=validated_data.get("password")
        )

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email"
        ]

class ProfileSerializer(serializers.ModelSerializer):
    working_unit = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = [
            "id",
            "nik",
            "name",
            "phone",
            "email",
            "gender",
            "working_unit"
        ]

    def get_working_unit(self, obj):
        if obj.working_unit:
            return {
                "name": obj.working_unit.name,
                "code": obj.working_unit.code,
                "level": obj.working_unit.level,
            }

class LoginSerializer(TokenObtainPairSerializer):        
    def validate(self, obj):
        data = super().validate(obj)

        data['user'] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email
        }

        return data