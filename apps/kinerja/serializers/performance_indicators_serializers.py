import json, re, ast
from decimal import Decimal
from datetime import datetime
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.exceptions import NotFound, ValidationError
from apps.kinerja.utils import create_log, _get_derived_values
from apps.kinerja.models import PerformanceTargets, PerformanceIndicators, AchievementTarget
from apps.api.models import WorkingUnit, Profile, Log, Title

class PerformanceIndicatorSerializer(serializers.ModelSerializer):
    unker_id = serializers.UUIDField(format='hex_verbose', required=True)
    title = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    parent_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    performance_targets_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    definition = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    data_source = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    validity = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    polarization = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    lower_limit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    upper_limit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    reference_indicator_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    calculation_data = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    state = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    calculation_method = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    calculation_method_detail = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    period = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    target = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    cascading_method = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    unit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    type = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    year = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    remaining_breakdown = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    cascading = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False
        ),
        required=False,
        allow_empty=True
    )
    is_priority = serializers.BooleanField(required=False)
    periodic_targets = serializers.DictField(default=dict, write_only=True, required=False, allow_null=True)
    action = serializers.CharField(required=True, allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = PerformanceIndicators
        fields = [
            "id",
            "unker_id",
            "title",
            "parent_id",
            "performance_targets_id",
            "definition",
            "data_source",
            "validity",
            "polarization",
            "lower_limit",
            "upper_limit",
            "reference_indicator_id",
            "calculation_data",
            "state",
            "calculation_method",
            "calculation_method_detail",
            "period",
            "target",
            "cascading_method", 
            "unit",
            "type",
            "year",
            "remaining_breakdown",       
            "cascading", 
            "is_priority",
            "periodic_targets",
            "action"
        ]

    @transaction.atomic
    def create(self, validated_data):
        periodic_targets = validated_data.pop("periodic_targets", {})

        reference_indicator = None
        reference_indicator_id = validated_data.pop("reference_indicator_id", None)
        if reference_indicator_id:
            reference_indicator = PerformanceIndicators.objects.filter(id=reference_indicator_id).first()
            if not reference_indicator:
                raise serializers.ValidationError("indicator previous year doesn't exists")
        
        parent = None
        parent_id = validated_data.pop("parent_id", None)
        if parent_id:
            parent = PerformanceIndicators.objects.filter(id=parent_id).first()
            if not parent:
                raise serializers.ValidationError("indicator parent doesn't exists")
        
        performance_target = None
        performance_targets_id = validated_data.pop("performance_targets_id", None)
        if performance_targets_id:
            performance_target = PerformanceTargets.objects.filter(id=performance_targets_id).first()
            if not performance_target:
                raise serializers.ValidationError("Performance Indicator doesn't exists")
        
        get_unker = validated_data.pop("unker_id", None)
        if get_unker:
            data_unker = WorkingUnit.objects.get(id=get_unker)
            if data_unker:
                if data_unker.level == '0':
                    perspektif = 'Internal Processes'
                else:
                    perspektif = None
                
                # set approver
                approver = []
                parent = data_unker.parent
                if parent:
                    officer = data_unker.title_set.first().officer.nik
                elif parent is None:
                    officer = data_unker.title_set.first().officer.nik
                approver = [officer]

        tahun = validated_data.get("year", None)

        # set approved state
        action = validated_data.pop("action").lower()
        print("action", action)
        if action == "submit":
            approved_status = "On Progress"
            sequence = 0
        elif action == "draft":
            approved_status = "Draft"
            sequence = -1

        validated_data.update({
            "unker": data_unker,
            "parent": parent,
            "reference_indicator": reference_indicator,
            "performance_targets": performance_target,
            "cascading": validated_data.get("cascading", []),
            "approver": approver,
            "approved_state": approved_status,
            "perspective": perspektif,
            "sequence": sequence,
        })

        instance = PerformanceIndicators.objects.create(**validated_data)

        def normalize_decimal(value):
            if value in ["", None]:
                return None
            return value

        # set target berkala
        AchievementTarget.objects.create(
            indicator   = instance,
            year        = tahun,
            category    = "Performance Indicator",
            tw1         = normalize_decimal(periodic_targets.get("tw1")),
            tw2         = normalize_decimal(periodic_targets.get("tw2")),
            tw3         = normalize_decimal(periodic_targets.get("tw3")),
            tw4         = normalize_decimal(periodic_targets.get("tw4")),
        )

        request = self.context.get("request")

        message = (
            f"[id: {instance.id}]"
            f"[action: {validated_data.get("action")}]"
        )
        log = create_log(request.user, "Create", "Performance Indicator", message)
        instance.logs.add(log)

        return instance
        
# class IndikatorOptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PerformanceIndicators
#         fields = "__all__"

# class UnitKerjaListSerializer(serializers.ModelSerializer):
#     code = serializers.SerializerMethodField()
#     name = serializers.SerializerMethodField()
#     level = serializers.SerializerMethodField()
#     level_baru = serializers.SerializerMethodField()
#     children = serializers.SerializerMethodField()

#     class Meta:
#         model = UnitKerja
#         fields = [
#             "id",
#             "code",
#             "name",
#             "level",
#             "level_baru",
#             "children",
#             'urutan',
#             'order'
#         ]

#     def get_code(self, obj):
#         return obj.unit_kerja_kode
    
#     def get_name(self, obj):
#         return obj.unit_kerja_nama
    
#     def get_level(self, obj):
#         return obj.unit_kerja_level
    
#     def get_level_baru(self, obj):
#         return penyesuaian_level(obj)
    
#     def get_children(self, obj):
#         data = _get_all_children(obj.unit_kerja_id)
#         return data
        
class IndikatorKinerjaSummarySerializer(serializers.ModelSerializer):
    jumlah_ik = serializers.SerializerMethodField()
    jumlah_ik_digunakan = serializers.SerializerMethodField()
    jumlah_ik_tidak_digunakan = serializers.SerializerMethodField()
    informasi = serializers.SerializerMethodField()

    class Meta:
        model = WorkingUnit
        fields = [
            "id",
            "name",
            "code",
            "level",
            "jumlah_ik",
            "jumlah_ik_digunakan",
            "jumlah_ik_tidak_digunakan",
            "informasi"
        ]

    def get_jumlah_ik(self, obj):
        return obj.jumlah_ik

    def get_jumlah_ik_digunakan(self, obj):
        return obj.jumlah_ik_digunakan

    def get_jumlah_ik_tidak_digunakan(self, obj):
        return obj.jumlah_ik_tidak_digunakan
    
    def get_informasi(self, obj):
        return {
            "on_progress": obj.on_progress,
            "approved": obj.approved,
            "rejected": obj.rejected,
            "need_revision": obj.need_revision,
            "revision_approved": obj.revision_approved,
            "revision_rejected": obj.revision_rejected,
            "locked": obj.locked_count,
        }

class IndikatorKinerjaDetailSerializer(serializers.ModelSerializer):
    working_unit = serializers.SerializerMethodField()
    performance_targets = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    reference_indicator = serializers.SerializerMethodField()
    achievement_targets = serializers.SerializerMethodField()
    cascading = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceIndicators
        fields = [
            "working_unit",
            "performance_targets",
            "parent",
            "reference_indicator",
            "achievement_targets",
            "title",
            "definition",
            "data_source",
            "validity",
            "polarization",
            "lower_limit",
            "upper_limit",
            "perspective", 
            "reference_indicator",
            "calculation_data",
            "state",  
            "calculation_method",
            "calculation_method_detail",
            "period",
            "target",
            "cascading_method",
            "unit",
            "type", 
            "year",
            "remaining_breakdown",
            "approver",
            "sequence",
            "approved_state",
            "is_priority",
            "cascading"
        
        ]

    def get_working_unit(self, obj):
        if obj.unker:
            print("unker", obj.unker)
            return {
                "id": obj.unker.id,
                "name": obj.unker.name,
                "code": obj.unker.code,
                "level": obj.unker.level,
            }
        return None
    
    def get_performance_targets(self, obj):
        if obj.performance_targets:
            return obj.performance_targets.title
        return None

    def get_parent(self, obj):
        if obj.parent:
            return {
                "id": obj.parent.id,
                "title": obj.parent.title
            }
        return None

    def get_reference_indicator(self, obj):
        if obj.reference_indicator:
            return {
                "id": obj.reference_indicator.id,
                "title": obj.reference_indicator.title
            }
        return None
    
    def get_achievement_targets(self, obj):
        data = AchievementTarget.objects.filter(indicator=obj, category="Performance Indicator").first()

        smt1, sd_tw3, sd_tw4 = _get_derived_values(data, obj.calculation_data)

        if not data:
            return {}

        return {
            "tw1": float(data.tw1) if data.tw1 is not None else None,
            "tw2": float(data.tw2) if data.tw2 is not None else None,
            "semester1": smt1,
            "tw3": float(data.tw3) if data.tw3 is not None else None,
            "s/d_tw3": sd_tw3,
            "tw4": float(data.tw4) if data.tw4 is not None else None,
            "s/d_tw4": sd_tw4,
        }
    
    def get_cascading(self, obj):
        result = []

        if obj.cascading:
            data = WorkingUnit.objects.filter(
                code__in=obj.cascading
            )
            for d in data:
                result.append({
                    "code": d.code,
                    "nama": d.name
                })

        return result

class IndikatorKinerjaDetailUpdateSerializer(serializers.ModelSerializer):
    unker_id = serializers.UUIDField(format='hex_verbose', required=True)
    title = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    parent_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    performance_targets_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    definition = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    data_source = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    validity = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    polarization = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    lower_limit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    upper_limit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    reference_indicator_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True, write_only=True)
    calculation_data = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    state = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    calculation_method = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    calculation_method_detail = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    period = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    target = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    cascading_method = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    unit = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    type = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    year = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    remaining_breakdown = serializers.CharField(required=True, allow_null=True, allow_blank=True)
    cascading = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
            allow_null=True,
            required=False
        ),
        required=False,
        allow_empty=True
    )
    is_priority = serializers.BooleanField(required=False)
    periodic_targets = serializers.DictField(default=dict, write_only=True, required=False, allow_null=True)
    action = serializers.CharField(required=True, allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = PerformanceIndicators
        fields = (
            "id",
            "unker_id",
            "title",
            "parent_id",
            "performance_targets_id",
            "definition",
            "data_source",
            "validity",
            "polarization",
            "lower_limit",
            "upper_limit",
            "reference_indicator_id",
            "calculation_data",
            "state",
            "calculation_method",
            "calculation_method_detail",
            "period",
            "target",
            "cascading_method", 
            "unit",
            "type",
            "year",
            "remaining_breakdown",       
            "cascading", 
            "is_priority",
            "periodic_targets",
            "action"
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        periodic_targets = validated_data.pop("periodic_targets", {})
        
        reference_indicator = None
        reference_indicator_id = validated_data.pop("reference_indicator_id", None)
        if reference_indicator_id:
            reference_indicator = PerformanceIndicators.objects.filter(id=reference_indicator_id).first()
            if not reference_indicator:
                raise serializers.ValidationError("indicator previous year doesn't exists")
        
        parent = None
        parent_id = validated_data.pop("parent_id", None)
        if parent_id:
            parent = PerformanceIndicators.objects.filter(id=parent_id).first()
            if not parent:
                raise serializers.ValidationError("indicator parent doesn't exists")
        
        performance_target = None
        performance_targets_id = validated_data.pop("performance_targets_id", None)
        if performance_targets_id:
            performance_target = PerformanceTargets.objects.filter(id=performance_targets_id).first()
            if not performance_target:
                raise serializers.ValidationError("Performance Indicator doesn't exists")
        
        get_unker = validated_data.pop("unker_id", None)
        if get_unker:
            data_unker = WorkingUnit.objects.get(id=get_unker)
            if data_unker:
                if data_unker.level == '0':
                    perspektif = 'Internal Processes'
                else:
                    perspektif = None
                
                # set approver
                approver = []
                parent = data_unker.parent
                if parent:
                    officer = data_unker.title_set.first().officer.nik
                elif parent is None:
                    officer = data_unker.title_set.first().officer.nik
                approver = [officer]

        tahun = validated_data.get("year", None)

        # set approved state
        action = validated_data.pop("action").lower()
        print("action", action)
        if action == "submit":
            approved_status = "On Progress"
            sequence = 0
        elif action == "draft":
            approved_status = "Draft"
            sequence = -1

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.approved_state=approved_status
        instance.sequence = sequence
        instance.save()

        def normalize_decimal(value):
            if value in ["", None]:
                return None
            return value

        target_obj = AchievementTarget.objects.filter(
            indicator=instance,
            category="Performance Indicator"
        ).first()

        def normalize_decimal(value):
            if value in ["", None]:
                return None
            return value

        if target_obj:
            target_obj.target = validated_data.get("target")
            target_obj.tw1 = normalize_decimal(periodic_targets.get("tw1"))
            target_obj.tw2 = normalize_decimal(periodic_targets.get("tw2"))
            target_obj.tw3 = normalize_decimal(periodic_targets.get("tw3"))
            target_obj.tw4 = normalize_decimal(periodic_targets.get("tw4"))
            target_obj.save()

        user = self.context.get("user")
        message = (
            f"[id: {instance.id}]"
        )
        create_log(user, "Update", "Performance Indicatorc", message)
        return instance
            
class ActionPerformanceIndicatorSerializer(serializers.ModelSerializer):
    id_indikator = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    action = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    komentar = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = PerformanceIndicators
        fields = [
            "id_indikator",
            "action",
            "komentar"
        ]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user")

        get_id_indicator = validated_data.get("id_indikator", [])
        get_action = validated_data.get("action", None)
        get_komentar = validated_data.get("komentar", None)

        queryset = PerformanceIndicators.objects.filter(is_delete=False)
        if get_id_indicator:
            queryset = queryset.filter(id__in=get_id_indicator)
            if queryset.count() != len(get_id_indicator):
                raise ValidationError(f"Data not found")
            
        for d in queryset:
            if d.approved_state not in ["On Progress", "Revision Requested"]:
                raise ValidationError(f"Document with id : {d.id} has been {d.approved_state}")

            # set notification
            d.extra_attributes = d.extra_attributes or {}
            d.extra_attributes["notification"] = True
            d.save()
            
            # get user request
            if get_action == "Approved":
                if d.approved_state == "Revision Requested":
                    log = Log.objects.create(
                        user=user,
                        action="Revision Approved",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Revision Approved] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                    # cek reference indicator
                    check = PerformanceIndicators.objects.filter(reference_indicator=d)
                    for c in check:
                        c.approved_state = "Locked"
                        c.save()

                    d.logs.add(log)
                    d.approved_state = "Revision Approved"
                    d.sequence = 1
                    d.save()
                else:
                    log = Log.objects.create(
                        user=user,
                        action="Approved",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Approved] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                    # cek reference indicator
                    check = PerformanceIndicators.objects.filter(reference_indicator=d)
                    for c in check:
                        c.approved_state = "On Progress"
                        c.save()

                    d.logs.add(log)
                    d.approved_state = "Approved"
                    d.sequence += 1
                    d.save()

            elif get_action == "Rejected":
                if d.approved_state == "Revision Requested":
                    log = Log.objects.create(
                        user=user,
                        action="Revision Rejected",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Revision Rejected] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                    # cek reference indicator
                    check = PerformanceIndicators.objects.filter(reference_indicator=d)
                    for c in check:
                        c.approved_state = "On Progress"
                        c.save()

                    d.logs.add(log)
                    d.approved_state = "Revision Rejected"
                    d.sequence = 0
                    d.save()
                else:
                    log = Log.objects.create(
                        user=user,
                        action="Rejected",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Rejected] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                    # cek reference indicator
                    check = PerformanceIndicators.objects.filter(reference_indicator=d)
                    for c in check:
                        c.approved_state = "On Progress"
                        c.save()

                    d.logs.add(log)
                    d.approved_state = "Rejected"
                    d.sequence = 0
                    d.save()
            elif get_action == "Submit":
                log = Log.objects.create(
                        user=user,
                        action="Submit",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Submit] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                d.logs.add(log)
                d.approved_state = "On Progress"
                d.sequence = 0
                d.save()

            elif get_action == "Need Revision":
                log = Log.objects.create(
                        user=user,
                        action="Need Revision",
                        feature_name="Performance Indicator",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Submit] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )

                d.logs.add(log)
                d.approved_state = "Need Revision"
                d.sequence = 0
                d.save()

        return f"{get_action} Performance Indicator successfully."
    
class getDialogHistorySerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    working_unit = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceIndicators
        fields = [
            "id",
            "profile",
            "working_unit",
            "history"
        ]
    
    def get_profile(self, obj):
        first_log = obj.logs.order_by("created_at").first()
        return first_log.user.profile_set.first().name if first_log and first_log.user.profile_set.first() else None
    
    def get_working_unit(self, obj):
        if obj.unker:
            return {
                "id": obj.unker.id,
                "code": obj.unker.code,
                "name": obj.unker.name,
            }
        return None
    
    def get_history(self, obj):
        request = self.context.get("request")
        get_type = request.query_params.get("type") if request else None

        logs = obj.logs.all().order_by("-created_at")

        if get_type == "Rejected":
            logs = logs.filter(action="Rejected")
        elif get_type == "Approved":
            logs = logs.filter(action="Approved")
        elif get_type == "Revision":
            logs = logs.filter(action__startswith="Revision")

        result = []

        for log in logs:
            approved_date = None
            notes = None

            if log.message:
                match_date = re.search(r'\[date:(.*?)\]', log.message)
                match_notes = re.search(r'\[notes:(.*?)\]', log.message)

                if match_date:
                    approved_date = match_date.group(1)

                if match_notes:
                    notes = match_notes.group(1)

            # set level 
            level = None
            if log.user.profile_set.first().working_unit:
                level = log.user.profile_set.first().working_unit.level

            result.append({
                "id": log.id,
                "action": log.action,
                "profile": log.user.profile_set.first().name if log.user.profile_set.first() else None,
                "nip": log.user.username if log.user else None,
                "unit_kerja_level": level,
                "message": log.message,
                "date": approved_date,
                "comment": notes,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })

        return result
    
class LogSerializer(serializers.ModelSerializer):
    id_indicator = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    changes_data = serializers.SerializerMethodField()
    edited_by = serializers.SerializerMethodField()
    log_date = serializers.SerializerMethodField()

    class Meta:
        model = Log
        fields = (
            "id",
            "action",
            "id_indicator",
            "state",
            "notes",
            "changes_data",
            "edited_by",
            "log_date",
        )

    def _parse_message(self, message):
        pattern = (
            r"\[(id_indicator|state|notes|changes|edited_by|date):(.*?)"
            r"(?=\[(?:id_indicator|state|notes|changes|edited_by|date):|\Z)"
        )
        matches = re.findall(pattern, message, re.DOTALL)
        result = {}
        for key, value in matches:
            result[key] = value.rstrip("]").strip()
        return result
    
    
    def parse_target_berkala(self, raw):
        pattern = r"'?\s*(\w+)\s*'?\s*:\s*(\d+)\s*->\s*([\d.]+)"
        result = {}
        raw = raw.strip().strip("{}")
        for item in raw.split(","):
            item = item.strip()
            match = re.match(pattern, item)
            if match:
                key = match.group(1)
                order = int(match.group(2))
                value = float(match.group(3))
                result[key] = f"{order} -> {value}"
        return result
    
    def get_id_indicator(self, obj):
        return self._parse_message(obj.message).get("id_indicator")

    def get_state(self, obj):
        return self._parse_message(obj.message).get("state")

    def get_notes(self, obj):
        return self._parse_message(obj.message).get("notes")

    def get_edited_by(self, obj):
        return self._parse_message(obj.message).get("edited_by")

    def get_log_date(self, obj):
        return self._parse_message(obj.message).get("date")

    def get_changes_data(self, obj):
        parsed = self._parse_message(obj.message)
        changes = parsed.get("changes", "")

        result = {}

        for item in changes.split(";"):
            item = item.strip()

            if ": " in item:
                key, value = item.split(": ", 1)

            elif item.startswith("notes:"):
                key = "notes"
                value = item[len("notes:"):]

            else:
                continue

            result[key.strip()] = value.strip()

            if key.strip() == "target_berkala":
                raw_value = value.strip()
                result["target_berkala"] = self.parse_target_berkala(raw_value)

                indicator_id = parsed.get("id_indicator")
                if indicator_id:
                    indicator_id = indicator_id.strip().rstrip("]")
                    target = AchievementTarget.objects.filter(indicator_id__id=indicator_id, category="Performance Indicator").first()
                    result["target_berkala"]["semester1"] = target.semester_satu_rata_rata()
                    result["target_berkala"]["s/d_tw3"] = target.tw_tiga_rata_rata()
                    result["target_berkala"]["s/d_tw4"] = target.semester_dua_rata_rata()

            if key.strip() == "parent":
                if value and value != "None":
                    data_ik = PerformanceIndicators.objects.get(pkid=value.strip())
                    result["indikator_tahun_sebelumnya"] = f"{data_ik.code} - {data_ik.title}"
                else:
                    result["indikator_tahun_sebelumnya"] = "Tidak Ada"

            if key.strip() == "reference_indicator":
                if value and value == "None":
                    result["reference_indicator"] = "Indirect Indicator"

                if value and value != "None":
                    raw_value = value.strip()

                    if " -> " in raw_value:
                        old_value, new_value = raw_value.split(" -> ", 1)
                    else:
                        old_value = None
                        new_value = raw_value

                    result["reference_indicator"] = {
                        "old": None,
                        "new": None,
                    }

                    if old_value and old_value != "None":
                        data_old = PerformanceIndicators.objects.filter(
                            pkid=old_value.strip()
                        ).first()

                        if data_old:
                            result["reference_indicator"]["old"] = (
                                f"{data_old.code} - {data_old.title}"
                            )

                    if new_value and new_value != "None":
                        data_new = PerformanceIndicators.objects.filter(
                            pkid=new_value.strip()
                        ).first()

                        if data_new:
                            result["reference_indicator"]["new"] = (
                                f"{data_new.code} - {data_new.title}"
                            )

            if key.strip() == "performance_targets":
               if value and value != "None":
                    data_ik = PerformanceTargets.objects.get(pkid=value.strip())
                    result["sasaran"] = f"{data_ik.code} - {data_ik.title}"

            if key.strip() == "unker":
               if value and value != "None":
                    data_unker = WorkingUnit.objects.get(pkid=value.strip())
                    result["unit_kerja_nama"] = data_unker.name
            if key.strip() == "year":
               if value and value != "None":
                    result["year"] = value.strip()[:4]
            
            if key.strip() == "cascading":
                data_cascading = []
                raw_value = value.strip()
                if raw_value.endswith("]]"):
                    raw_value = raw_value[:-1]

                cascading_list = ast.literal_eval(raw_value)

                data = WorkingUnit.objects.filter(code__in=cascading_list)
                for d in data:
                    data_cascading.append({
                        "code": d.code,
                        "nama": d.name
                    })

                result["cascading"] = data_cascading
        return result
    
class RequestRevisionPerformanceIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceIndicators
        fields = "__all__"

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user")

        # permission check
        get_users = Title.objects.filter(unker=instance.unker, officer__nik=user.username)
        if not get_users:
            raise ValidationError(
                "You do not have permission to edit this indicator."
            )

        # validation state
        if instance.approved_state != "Approved":
            raise ValidationError(
                f"Document with id {instance.id} cannot be revised."
            )

        # set notification
        instance.extra_attributes = instance.extra_attributes or {}
        instance.extra_attributes["notification"] = True
        instance.save()

        if instance.approved_state == "Approved":
            log = Log.objects.create(
                user=user,
                action="Revision Requested",
                feature_name="Performance Indicator",
                message=(
                    f"[id_indicator:{instance.id}] "
                    f"[state:Revision Requested] "
                    f"[notes:{user.username} - {user.profile_set.first().name} mengajukan permohonan revisi pada indikator {instance.title}] "
                    f"[date:{datetime.now()}]"
                )
            )

            instance.logs.add(log)
            instance.approved_state = "Revision Requested"
            instance.sequence = 0
            instance.save()

        return {
            "message": f"Revision request for indicator with id {instance.id} submitted successfully."
        }
    
class EditRevisionPerformanceIndicatorSerializer(serializers.ModelSerializer):
    reference_indicator = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    performance_target = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tahun = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    target_berkala = serializers.DictField(default=dict, write_only=True)

    class Meta:
        model = PerformanceIndicators
        fields = "__all__"

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user")

        # permission check
        get_users = Title.objects.filter(unker=instance.unker).select_related("officer")
        has_permission = False

        for title in get_users:
            if not title.officer:
                continue

            officer = title.officer.nik
            if user.username == officer:
                has_permission = True
                break

        if not has_permission:
            raise ValidationError(
                "You do not have permission to edit this indicator."
            )

        # validation state
        if instance.approved_state not in ["Revision Approved", "Need Revision"]:
            raise ValidationError(
                f"Cannot edit this indicator because the status not Revision Approved or Need Revision."
            )
        
        # before
        before = {}
        
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            if hasattr(value, "pk"):
                value = value.pk

            before[field.name] = value
        
        performance_target_id = validated_data.pop("performance_target", None)
        reference_indicator_id = validated_data.pop("reference_indicator", None)
        target_berkala = validated_data.pop("target_berkala", {})
        year = validated_data.pop("year", None)
        
        if year:
            instance.year = year
            instance.save()

        old_data = {}
        new_data = {}
        
        # resolve FK -> object
        if performance_target_id:
            instance.performance_targets = PerformanceTargets.objects.get(id=performance_target_id)
        elif performance_target_id == "":
            instance.performance_targets = None

        if reference_indicator_id:
            instance.reference_indicator = PerformanceIndicators.objects.get(id=reference_indicator_id)
        elif reference_indicator_id == "":
            instance.reference_indicator = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # get profile user
        get_user = Profile.objects.filter(nik=user.username).first()

        # after
        after = {}

        for field in instance._meta.fields:
            value = getattr(instance, field.name)

            if hasattr(value, "pk"):
                value = value.pk

            after[field.name] = value

        changes = []
            
        if target_berkala:
            # detect target berkala
            old_achievement = AchievementTarget.objects.filter(indicator=instance, category="Performance Indicator").first()
            old_tw =  {}
            if old_achievement:
                old_tw = {
                    "tw1": old_achievement.tw1,
                    "tw2": old_achievement.tw2,
                    "tw3": old_achievement.tw3,
                    "tw4": old_achievement.tw4,
                    
                }

            achievement, created = AchievementTarget.objects.update_or_create(
                indicator=instance,
                year=instance.year,
                category="Performance Indicator",
                defaults={
                    "tw1": target_berkala.get("tw1"),
                    "tw2": target_berkala.get("tw2"),
                    "tw3": target_berkala.get("tw3"),
                    "tw4": target_berkala.get("tw4"),
                }
            )

            new_tw = {
                "tw1": achievement.tw1,
                "tw2": achievement.tw2,
                "tw3": achievement.tw3,
                "tw4": achievement.tw4,
            }

            tw_changes = []
            for key in ["tw1", "tw2", "tw3", "tw4"]:
                old_val = old_tw.get(key)
                new_val = new_tw.get(key)
                if isinstance(old_val, Decimal):
                    old_val = int(old_val)

                if isinstance(new_val, Decimal):
                    new_val = int(new_val)

                if old_val != new_val:
                    tw_changes.append(f"'{key}': {old_val} -> {new_val}")
            if tw_changes:
                changes.append(f"target_berkala: {{ {', '.join(tw_changes)} }}")


        for field_name in before.keys():
            old_val = before.get(field_name)
            new_val = after.get(field_name)

            if old_val != new_val:
                changes.append(f"{field_name}: {old_val} -> {new_val}")
            else:
                changes.append(f"{field_name}: {old_val}")


        log = Log.objects.create(
            user=user,
            action="Update",
            feature_name="Performance Indicator",
            message=(
                f"[id_indicator:{instance.id}] "
                f"[state:Revision] "
                f"[notes:{user.profile_set.first().name} telah memperbarui data.]"
                f"[changes: {'; '.join(changes) if changes else 'No changes'}] "
                f"[edited_by:{user.username} - {user.profile_set.first().name}] "
                f"[date:{datetime.now()}]"
            )
        )

        instance.logs.add(log)
        instance.approved_state = "On Progress"
        instance.sequence = 0
        instance.extra_attributes = instance.extra_attributes or {}
        instance.extra_attributes["notification"] = True
        instance.save()

        return {
            "message": "Edit Revision Performance Indicator successfully."
        }