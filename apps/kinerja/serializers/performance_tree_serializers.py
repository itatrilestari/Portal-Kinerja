from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.kinerja.models import PerformanceIndicators, AchievementTarget, PerformanceTargets

class PohonKinerjaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceIndicators
        fields = [
            "id",
            "title",
        ]

class PohonKinerjaDetailSerializer(serializers.ModelSerializer):
    sasaran_id = serializers.SerializerMethodField()
    sasaran_title = serializers.SerializerMethodField()
    indicator_id = serializers.SerializerMethodField()
    indicator_title = serializers.SerializerMethodField()
    target_berkala = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceIndicators
        fields = [
            "sasaran_id",
            "sasaran_title",
            "indicator_id",
            "indicator_title",
            "polarization",
            "unit",
            "period",
            "target",
            "target_berkala",
            "calculation_data",
        ]

    def get_sasaran_id(self, obj):
        if obj.performance_targets:
            return str(obj.performance_targets.id)
        return None

    def get_sasaran_title(self, obj):
        if obj.performance_targets:
            return obj.performance_targets.title
        return None

    def get_indicator_id(self, obj):
        if obj.id:
            return str(obj.id)
        return None

    def get_indicator_title(self, obj):
        if obj.title:
            return obj.title
        return None

    def get_target_berkala(self, obj):
        data = AchievementTarget.objects.filter(indicator=obj, category="Performance Indicator").first()
        
        if not data:
            return {}

        return {
            "tw1": float(data.tw1) if data.tw1 is not None else None,
            "tw2": float(data.tw2) if data.tw2 is not None else None,
            "tw3": float(data.tw3) if data.tw3 is not None else None,
            "tw4": float(data.tw4) if data.tw4 is not None else None,
        }

class PohonKinerjaMindmapSerializer(serializers.Serializer):
    working_unit_code = serializers.SerializerMethodField()
    working_unit_name = serializers.SerializerMethodField()
    sasaran_id = serializers.CharField(source='id')
    sasaran_title = serializers.CharField(source='title')
    indicator = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceTargets
        fields = [
            "working_unit_code",
            "working_unit_name",
            "sasaran_id",
            "sasaran_title",
            "indicator",
        ]

    def get_working_unit_code(self, obj):
        if obj.working_unit:
            return obj.working_unit.code
        return None

    def get_working_unit_name(self, obj):
        if obj.working_unit:
            return obj.working_unit.name
        return None

    def get_indicator(self, obj):
        indicators = obj.performanceindicators_set.filter(is_delete=False).order_by('created_at')
        return [
            {"indicator_id": str(i.id), "indicator_title": i.title}
            for i in indicators
        ]