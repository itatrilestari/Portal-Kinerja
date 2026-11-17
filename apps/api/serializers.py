from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.api.models import Profile, Title, WorkingUnit
from apps.kinerja.utils import create_log

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

class TitleSerializer(serializers.ModelSerializer):
    display_title = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    officer_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    unker_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)

    class Meta:
        model = Title
        fields = [
            "display_title",
            "officer_id",
            "unker_id"
        ]

    @transaction.atomic
    def create(self, validated_data):
        get_officer_id = validated_data.pop("officer_id")
        get_unker_id = validated_data.pop("unker_id")

        if get_officer_id:
            officer = Profile.objects.filter(id=get_officer_id).first()
            if not officer:
                raise serializers.ValidationError("Officer not found")

        if get_unker_id:
            unker = WorkingUnit.objects.filter(id=get_unker_id).first()
            if not unker:
                raise serializers.ValidationError("Working Unit not found")

        title = Title.objects.create(
            officer = officer,
            unker = unker,
            **validated_data
        )

        request = self.context.get("request")
        message = f"[id: {title.id}]"
        create_log(request.user, "Create", "Title", message=message)

        return title
