import os
import uuid
from datetime import datetime
from rest_framework import serializers
from apps.api.models import Attachment, WorkingUnit
from apps.kinerja.models import PerformanceDocument
from apps.kinerja.utils import create_log

class AttachmentSerializer(serializers.ModelSerializer):
    file_path = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "filename", 
            "file", 
            "file_size",
            "file_path"
        ]


    def get_file_path(self, obj):
        return obj.file.path if obj.file else None
    
    def get_file_size(self, obj):
        return obj.file.size if obj.file else None

class PerformanceDocumentSerializer(serializers.ModelSerializer):
    working_unit = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, source="attachment")

    class Meta:
        model = PerformanceDocument
        fields = [
            "id",
            "working_unit",
            "category",
            "notes",
            "attachments"
        ]
    
    def get_working_unit(self, obj):
        if obj.unker:
            return {
                "code": obj.unker.code,
                "name": obj.unker.name,
                "level": obj.unker.level
            }
        return None
        
    def get_category(self, obj):
        return obj.category
    
    def get_notes(self, obj):
        return obj.notes

class PerformanceDocumentListSerializer(serializers.ModelSerializer):
    pohon_kinerja = serializers.SerializerMethodField()
    renstrai = serializers.SerializerMethodField()
    renja = serializers.SerializerMethodField()
    pk = serializers.SerializerMethodField()
    sk_indikator_kinerja = serializers.SerializerMethodField()
    manual_indikator_kinerja = serializers.SerializerMethodField()
    matrix_cascading_mph = serializers.SerializerMethodField()
    rencana_aksi = serializers.SerializerMethodField()
    rincian_target_indikator = serializers.SerializerMethodField()
    laporan_kinerja_tw1 = serializers.SerializerMethodField()
    laporan_kinerja_tw2 = serializers.SerializerMethodField()
    laporan_kinerja_tw3 = serializers.SerializerMethodField()
    laporan_kinerja_tw4 = serializers.SerializerMethodField()
    evaluasi_kinerja_tw1 = serializers.SerializerMethodField()
    evaluasi_kinerja_tw2 = serializers.SerializerMethodField()
    evaluasi_kinerja_tw3 = serializers.SerializerMethodField()
    evaluasi_kinerja_tw4 = serializers.SerializerMethodField()

    class Meta:
        model = WorkingUnit
        fields = [
            "id",
            "level",
            "code",
            "name",
            "pohon_kinerja",
            "renstrai",
            "renja",
            "pk",
            "sk_indikator_kinerja",
            "manual_indikator_kinerja",
            "matrix_cascading_mph",
            "rencana_aksi",
            "rincian_target_indikator",
            "laporan_kinerja_tw1",
            "laporan_kinerja_tw2",
            "laporan_kinerja_tw3",
            "laporan_kinerja_tw4",
            "evaluasi_kinerja_tw1",
            "evaluasi_kinerja_tw2",
            "evaluasi_kinerja_tw3",
            "evaluasi_kinerja_tw4"
        ]
        
    def get_pohon_kinerja(self, obj):
        return obj.pohon_kinerja
    
    def get_renstrai(self, obj):
        return obj.renstrai
    
    def get_renja(self, obj):
        return obj.renja

    def get_pk(self, obj):
        return obj.pk

    def get_sk_indikator_kinerja(self, obj):
        return obj.sk_indikator_kinerja

    def get_manual_indikator_kinerja(self, obj):
        return obj.manual_indikator_kinerja

    def get_matrix_cascading_mph(self, obj):
        return obj.matrix_cascading_mph

    def get_rencana_aksi(self, obj):
        return obj.rencana_aksi

    def get_rincian_target_indikator(self, obj):
        return obj.rincian_target_indikator

    def get_laporan_kinerja_tw1(self, obj):
        return obj.laporan_kinerja_tw1

    def get_laporan_kinerja_tw2(self, obj):
        return obj.laporan_kinerja_tw2

    def get_laporan_kinerja_tw3(self, obj):
        return obj.laporan_kinerja_tw3

    def get_laporan_kinerja_tw4(self, obj):
        return obj.laporan_kinerja_tw4

    def get_evaluasi_kinerja_tw1(self, obj):
        return obj.evaluasi_kinerja_tw1

    def get_evaluasi_kinerja_tw2(self, obj):
        return obj.evaluasi_kinerja_tw2

    def get_evaluasi_kinerja_tw3(self, obj):
        return obj.evaluasi_kinerja_tw3

    def get_evaluasi_kinerja_tw4(self, obj):
        return obj.evaluasi_kinerja_tw4
    
class PerformanceDocumentCreateSerializer(serializers.ModelSerializer):
    ALLOWED_CATEGORIES = {
        'Pohon Kinerja',
        'Renstra',
        'Renja',
        'PK',
        'SK Indikator Kinerja',
        'Manual Indikator Kinerja',
        'Matrix Cascading / MPH',
        'Rencana Aksi',
        'Rincian Target Indikator',
        'Laporan Kinerja TW I',
        'Laporan Kinerja TW II',
        'Laporan Kinerja TW III',
        'Laporan Kinerja TW IV',
        'Evaluasi Kinerja TW I',
        'Evaluasi Kinerja TW II',
        'Evaluasi Kinerja TW III',
        'Evaluasi Kinerja TW IV',
    }

    unker = serializers.CharField(write_only=True, required=False)
    notes = serializers.CharField(max_length=2000, write_only=True, required=False)
    category = serializers.CharField(write_only=True, required=True)
    year = serializers.CharField(write_only=True, required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = PerformanceDocument
        fields = [
            "unker",
            "notes",
            "category",
            "attachments",
            "year"
        ]

    def validate_category(self, value):
        if value not in self.ALLOWED_CATEGORIES:
            raise serializers.ValidationError("Category tidak termasuk dalam daftar dokumen yang tersedia.")
        
        return value

    def create(self, validated_data):
        get_unker = validated_data.get("unker", None)
        get_notes = validated_data.get("notes", None)
        get_category = validated_data.get("category", None)
        get_year = validated_data.get("year", None)
        get_attachments = validated_data.pop("attachments", [])

        # set unker
        unkers = WorkingUnit.objects.filter(id=get_unker).first()

        year_now = datetime.now().year
        random_id = uuid.uuid4().hex

        instance = PerformanceDocument.objects.create(
            unker = unkers,
            category = get_category,
            notes = get_notes,
            year = get_year
        )
        
        for file in get_attachments:
            custom_filename = (f"{get_category}_{year_now}{random_id}")
            attachment = Attachment.objects.create(
                file=file,
                filename=custom_filename
            )

            instance.attachment.add(attachment)

        user = self.context.get("user")
        message = f"[id: {instance.id}]"
        create_log(user, "Create", "Performance Document", message)
        return instance
    
    def to_representation(self, instance):
        return PerformanceDocumentSerializer(instance).data
