import re
import ast
from datetime import datetime
from rest_framework import serializers
from apps.kinerja.models import Recommendation, Resolution, PerformanceIndicators
from apps.api.models import WorkingUnit, Title, Profile, Log
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Q
from apps.kinerja.utils import create_log

class RecommendationSummarySerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    badge = serializers.SerializerMethodField()

    class Meta:
        model = WorkingUnit
        fields = [
            "id",
            "level",
            "code",
            "name",
            "parent",
            "badge",
        ]

    def get_parent(self, obj):
        if obj.parent:
            return obj.parent.name
        return None
        
    def get_badge(self, obj):
        return {
            "jumlah_rekomendasi": obj.jumlah_rekomendasi,
            "jumlah_tindak_lanjut": obj.jumlah_tindak_lanjut,
            "jumlah_tuntas": obj.jumlah_tuntas,
            "jumlah_on_progress": obj.jumlah_on_progress
        }

class RecommendationSerializer(serializers.ModelSerializer):
    id_rekomendasi = serializers.SerializerMethodField()
    rekomendasi = serializers.SerializerMethodField()
    badge = serializers.SerializerMethodField()

    class Meta:
        model = WorkingUnit
        fields = [
            "id_rekomendasi",
            "rekomendasi",
            "badge",
        ]
        
    def get_id_rekomendasi(self, obj):
        if obj.id:
            return str(obj.id)
        
    def get_rekomendasi(self, obj):
        if obj.instruction:
            return obj.instruction
        
    def get_badge(self, obj):
        data =  Resolution.objects.filter(
            recommendation_id=obj.pkid,
            is_delete=False
        ).aggregate(
            jumlah_tindak_lanjut=Count("id"),
            jumlah_tuntas=Count("id", filter=Q(status="Tuntas")),
            jumlah_on_progress=Count("id", filter=Q(status="On Progress")),
        )

        return data
        

class RecommendationAllSerializer(serializers.ModelSerializer):
    unit_kerja_id = serializers.SerializerMethodField()
    unit_kerja_nama = serializers.SerializerMethodField()
    unit_kerja_kode = serializers.SerializerMethodField()
    tahun = serializers.SerializerMethodField()
    id_rekomendasi = serializers.SerializerMethodField()
    rekomendasi = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "unit_kerja_id",
            "unit_kerja_nama",
            "unit_kerja_kode",
            "tahun",
            "id_rekomendasi",
            "rekomendasi",
            "approver",
        ]

    def get_unit_kerja_id(self, obj):
        if obj.unker:
            return str(obj.unker.id)
        return None

    def get_unit_kerja_nama(self, obj):
        if obj.unker:
            return obj.unker.name
        return None
    
    def get_unit_kerja_kode(self, obj):
        if obj.unker:
            return obj.unker.code
        return None
        
    def get_tahun(self, obj):
        if obj.year:
            return obj.year
        return None
    
    def get_id_rekomendasi(self, obj):
        if obj.id:
            return str(obj.id)
        return None
    
    def get_rekomendasi(self, obj):
        if obj.instruction:
            return obj.instruction
        return None
    
    def get_approver(self, obj):
        if obj.approver:
            return obj.approver
        return None

class TindakLanjutListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    tindak_lanjut = serializers.SerializerMethodField()
    approver = serializers.SerializerMethodField()
    status_verifikasi = serializers.SerializerMethodField()
    komentar = serializers.SerializerMethodField()
    notification = serializers.SerializerMethodField()

    class Meta:
        model = Resolution
        fields = [
            "id",
            "status",
            "url",
            "tindak_lanjut",
            "approver",
            "status_verifikasi",
            "komentar",
            "notification"
        ]

    def get_status(self, obj):
        if obj.status:
            return obj.status
        return None
    
    def get_url(self, obj):
        if obj.url:
            return obj.url
        return None
    
    def get_tindak_lanjut(self, obj):
        if obj.action:
            return obj.action
        return None
    
    def get_approver(self, obj):
        if obj.recommendation:
            data = Recommendation.objects.get(id=obj.recommendation.id).approver
            return data
        return None
    
    def get_status_verifikasi(self, obj):
        if obj.verification_state:
            return obj.verification_state
        return None
    
    def get_komentar(self, obj):
        return [
            {
                "action": log.action,
                "message": log.message,
                "created_at": log.created_at
            }
            for log in obj.logs.all()
        ]

    def get_notification(self, obj):
        if obj.extra_attributes:
            return obj.extra_attributes.get("notification")
        return None

class RecommendationCreateSerializer(serializers.ModelSerializer):
    unker = serializers.CharField(write_only=True, required=False)
    tahun = serializers.CharField(write_only=True, required=False)
    rekomendasi = serializers.CharField(max_length=2000, write_only=True, required=False)
    tindak_lanjut = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "unker",
            "tahun",
            "rekomendasi",
            "tindak_lanjut"
        ]

    def create(self, validated_data):
        user = self.context.get("user")
        get_unker = validated_data.get("unker", None)
        get_tahun = validated_data.get("tahun", None)
        get_rekomendasi = validated_data.get("rekomendasi", None)
        tindak_lanjut = validated_data.pop("tindak_lanjut", [])

        data_unker = WorkingUnit.objects.get(id=get_unker)

        # set approver
        approver = []

        parent = data_unker.parent or data_unker
        title = Title.objects.filter(unker=parent, is_delete=False).first()

        if title and title.officer and title.officer.nik:
            nik = title.officer.nik

            if isinstance(nik, str):
                nik = ast.literal_eval(nik) if nik.startswith('[') else [nik]

            approver = nik

        data_rekomendasi = Recommendation.objects.create(
            unker       = data_unker,
            year        = get_tahun,
            instruction = get_rekomendasi,
            approver    = [approver],
        )

        message = f"[id: {data_rekomendasi.id}]"
        create_log(user, "Create", "Recommendation", message)

        tindak_lanjut_id = []
        for item in tindak_lanjut:
            data_tindak_lanjut = Resolution.objects.create(
                recommendation  = data_rekomendasi,
                status          = item.get("status"),
                url             = item.get("url"),
                action          = item.get("action"),
                verification_state  = "On Progress"
            )

            tindak_lanjut_id.append(data_tindak_lanjut.id)

        message = f"[id: {', '.join(str(id) for id in tindak_lanjut_id)}]"
        create_log(user, "Create", "Resolution", message)
        
        return data_rekomendasi
    
    def to_representation(self, instance):
        return RecommendationAllSerializer(instance).data
    
class RecommendationCreateRekomendasiSerializer(serializers.ModelSerializer):
    unker = serializers.CharField(write_only=True, required=False)
    rekomendasi = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "unker",
            "rekomendasi",
        ]

    def create(self, validated_data):
        user = self.context.get("user")
        get_unker = validated_data.get("unker", None)
        get_rekomendasi = validated_data.get("rekomendasi", [])

        data_unker = WorkingUnit.objects.filter(id=get_unker).first()

        # set approver
        approver = []

        parent = data_unker.parent or data_unker
        title = Title.objects.filter(unker=parent, is_delete=False).first()

        if title and title.officer and title.officer.nik:
            nik = title.officer.nik

            if isinstance(nik, str):
                nik = ast.literal_eval(nik) if nik.startswith('[') else [nik]

            approver = nik

        rekomendasi_id = []
        for item in get_rekomendasi:
            data_rekomendasi = Recommendation.objects.create(
                unker       = data_unker,
                year        = item.get("tahun"),
                instruction = item.get("rekomendasi"),
                approver    = [approver],
            )
            rekomendasi_id.append(data_rekomendasi.id)

        message = f"[id: {', '.join(str(id) for id in rekomendasi_id)}]"
        create_log(user, "Create", "Recommendation", message)
        
        return data_rekomendasi
    
    def to_representation(self, instance):
        return RecommendationAllSerializer(instance).data
    
class RecommendationDetailSerializer(serializers.ModelSerializer):
    unker = serializers.CharField(write_only=True, required=False)
    tahun = serializers.CharField(write_only=True, required=False)
    rekomendasi = serializers.CharField(max_length=2000, write_only=True, required=False)
    tindak_lanjut = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "unker",
            "tahun",
            "rekomendasi",
            "tindak_lanjut"
        ]

    def update(self, instance, validated_data):
        get_unker = validated_data.get("unker")
        get_tahun = validated_data.get("tahun")
        get_rekomendasi = validated_data.get("rekomendasi")
        tindak_lanjut = validated_data.pop("tindak_lanjut", [])

        existing_resolutions = list(
            Resolution.objects.filter(
                recommendation=instance,
                is_delete=False
            )
        )

        if get_unker:
            data_unker = WorkingUnit.objects.get(id=get_unker)
        else:
            data_unker = WorkingUnit.objects.get(id=instance.unker.id)
        
        instance.unker = data_unker

        if get_tahun:
            instance.year = get_tahun

        if get_rekomendasi:
            instance.instruction = get_rekomendasi

        instance.save()

        for item in tindak_lanjut:
            resolution_id = item.get("id")

            if resolution_id:
                # update
                resolution = Resolution.objects.get(
                    id=resolution_id,
                    recommendation=instance
                )

                resolution.status = item.get("status")

                if item.get("status") == "Tuntas":
                    print(item.get("status"))
                    resolution.verification_state = "Need Verificated"
                else:
                    resolution.verification_state = "On Progress"
                resolution.url = item.get("url")
                resolution.action = item.get("action")
                if resolution.extra_attributes is None:
                    resolution.extra_attributes = {}
    
                resolution.extra_attributes["notification"] = True
                resolution.save()

            else:
                # create
                Resolution.objects.create(
                    recommendation=instance,
                    status=item.get("status"),
                    url=item.get("url"),
                    action=item.get("action"),
                    verification_state="On Progress"
                )
        user = self.context.get("user")
        message = f"[id: {instance.id}]"
        create_log(user, "Update", "Recommendation and Resolution", message)

        return instance
    
class ActionResolutionSerializer(serializers.ModelSerializer):
    id_tindak_lanjut = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    action = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    komentar = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = PerformanceIndicators
        fields = [
            "id_tindak_lanjut",
            "action",
            "komentar"
        ]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user")

        get_id_tindak_lanjut = validated_data.get("id_tindak_lanjut", [])
        get_action = validated_data.get("action", None)
        get_komentar = validated_data.get("komentar", None)

        get_tindak_lanjut = Resolution.objects.filter(id__in=get_id_tindak_lanjut)
        get_user = Profile.objects.get(nik=user)
        
        for d in get_tindak_lanjut:
            if user.username not in d.recommendation.approver:
                raise ValidationError(f"You dont have permission to verify {d.action}.")
            
            if d.status != "Tuntas":
                raise ValidationError('You cannot verify this Resolution because the status is still "On Progress".')
            
            if d.verification_state == "Verificated":
                raise ValidationError("You cannot verify this resolution because it has already been verified.")

            if d.extra_attributes is None:
                d.extra_attributes = {}

            d.extra_attributes["notification"] = True
            d.save()
            
            if get_action == "Approved":
                log = Log.objects.create(
                        user=get_user if get_user else None,
                        action="Approved",
                        feature_name="Recommendation and Resolution",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Approved] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )
                d.status = "Tuntas"
                d.verification_state = "Verificated"
                d.logs.add(log)
                d.save()
            if get_action == "Rejected":
                log = Log.objects.create(
                        user=get_user if get_user else None,
                        action="Rejected",
                        feature_name="Recommendation and Resolution",
                        message = (
                            f"[id_indicator:{d.id}] "
                            f"[state:Rejected] "
                            f"[notes:{get_komentar}]"
                            f"[date:{datetime.now()}]"
                        )
                    )
                d.status = "On Progress"
                d.verification_state = "On Progress"
                d.logs.add(log)
                d.save()

        return f"{get_action} Resolution successfully."

class getDialogHistoryResolutionSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    working_unit = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta:
        model = Resolution
        fields = [
            "id",
            "profile",
            "working_unit",
            "history"
        ]

    def get_id(self, obj):
        return str(obj.id)
    
    def get_profile(self, obj):
        first_log = obj.logs.order_by("created_at").first()
        return first_log.profile.nama if first_log and first_log.profile else None
    
    def get_working_unit(self, obj):
        if obj.recommendation:
            data_recommendation = Recommendation.objects.get(pkid=obj.recommendation.pkid)
            if data_recommendation:
                return data_recommendation.unker.name
            return None
    
    def get_history(self, obj):
        request = self.context.get("request")
        get_type = request.query_params.get("type") if request else None

        logs = obj.logs.all().order_by("-created_at")

        if get_type == "Rejected":
            logs = logs.filter(action="Rejected Verification Resolution")
        elif get_type == "Approved":
            logs = logs.filter(action="Approved Verification Resolution")

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

            result.append({
                "id": log.id,
                "action": log.action,
                "profile": log.profile.name if log.profile else None,
                "nip": log.profile.nik if log.profile else None,
                "unit_kerja_level": log.profile.workint_unit.level if log.profile else None,
                "message": log.message,
                "date": approved_date,
                "comment": notes,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })

        return result