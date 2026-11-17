from rest_framework import serializers
from django.db import transaction
from apps.kinerja.models import PerformanceTargets
from apps.api.models import WorkingUnit
from apps.kinerja.utils import create_log

class PerformanceTargetRequestSerializer(serializers.ModelSerializer):
    working_unit_id = serializers.UUIDField(format='hex_verbose', required=True, write_only=True)
    parent_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    year = serializers.IntegerField(required=True)
    title = serializers.CharField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = PerformanceTargets
        fields = [
            "id",
            "working_unit_id",
            "parent_id",
            "year",
            "title",
            "status"
        ]

    @transaction.atomic
    def create(self, validated_data):
        working_unit_id = validated_data.pop("working_unit_id", None)
        parent_id = validated_data.pop("parent_id", None)

        working_unit = None
        parent = None

        if working_unit_id:
            working_unit = WorkingUnit.objects.filter(id=working_unit_id).first()
            if not working_unit:
                raise serializers.ValidationError("Working unit not found")

        if parent_id:
            parent = PerformanceTargets.objects.filter(id=parent_id).first()
            if not parent:
                raise serializers.ValidationError("Performance Target not found")

        performance_targets = PerformanceTargets.objects.create(
            working_unit = working_unit,
            parent = parent,
            **validated_data
        )

        message = f"[id: {performance_targets.id}]"
        request = self.context.get("request")

        log = create_log(request.user, "Create", "Performance Targets", message)
        if log:
            performance_targets.logs.add(log)

        return performance_targets

    @transaction.atomic
    def update(self, instance, validated_data):
        working_unit_id = validated_data.pop("working_unit_id", None)
        parent_id = validated_data.pop("parent_id", None)

        working_unit = None
        parent = None

        if working_unit_id:
            working_unit = WorkingUnit.objects.filter(id=working_unit_id).first()
            if not working_unit:
                raise serializers.ValidationError("Working unit not found")

        if parent_id:
            parent = PerformanceTargets.objects.filter(id=parent_id).first()
            if not parent:
                raise serializers.ValidationError("Performance Target not found")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        message = f"[id: {instance.id}]"
        request = self.context.get("request")

        log = create_log(request.user, "Update", "Performance Targets", message)
        instance.logs.add(log)

        return instance

class PerformanceTargetsSerializer(serializers.ModelSerializer):
    working_unit = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceTargets
        fields = [
            "id",
            "year",
            "title",
            "status",
            "working_unit",
            "parent"
        ]

    def get_working_unit(self, obj):
        if obj.working_unit:
            return {
                "id": obj.working_unit.id,
                "name": obj.working_unit.name,
                "code": obj.working_unit.code
            }
        return None

    def get_parent(self, obj):
        if obj.parent:
            if obj.parent.is_delete == False:
                return PerformanceTargetsSerializer(obj.parent, context=self.context).data
        return None