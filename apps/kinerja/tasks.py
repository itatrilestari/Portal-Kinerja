from celery import shared_task
from django.core.files.base import ContentFile
from apps.api.models import ExportJob, WorkingUnit
from apps.kinerja.utils import *

# performance indicators
@shared_task()
def generate_matrix_target(job_id, unker_id, year):
    job = ExportJob.objects.filter(id=job_id).first()

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        if unker_id:
            unker = WorkingUnit.objects.filter(id=unker_id).first()

        export_doc = export_matrix_target(unker_id, year)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"MATRIKS_TARGET_{unker.name}_{year}.xlsx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise

@shared_task
def generate_rincian_indikator(job_id, unker_id, year, unker_nama):
    job = ExportJob.objects.filter(id=job_id).first()

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        export_doc = export_rincian_indikator(unker_id, year, unker_nama)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"DATA_PERENCANAAN_KINERJA_{unker_nama.upper()}_{year}.xlsx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise

@shared_task
def generate_rincian_target(job_id, unker_id, year, unker_nama):
    job = ExportJob.objects.filter(id=job_id).first()

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        # if unker_id:
        #     unker = UnitKerja.objects.filter(id=unker_id).first()

        export_doc = export_file_rincian_target(unker_id, year, unker_nama)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"RINCIAN_TARGET_{unker_nama.upper()}_{year}.docx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise

@shared_task
def generate_penetapan_indicator(job_id, unker_id, year, unker_nama):
    job = ExportJob.objects.filter(id=job_id).first()

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        export_doc = export_file_penetapan_indikator(unker_id, year, unker_nama)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"PENETAPAN_INDIKATOR_KINERJA_{unker_nama.upper()}_{year}.docx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise

@shared_task
def generate_capaian_indicator(job_id, unker_id, year, tw, unker_nama):
    job = ExportJob.objects.filter(id=job_id).first()

    if not job:
        raise ValueError(f"ExportJob dengan ID {job_id} tidak ditemukan")

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        export_doc = generate_capaian_indikator(unker_id, year, tw, unker_nama)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"CAPAIAN_INDIKATOR_KINERJA_{unker_nama.upper()}_{year}.xlsx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise

# performance document
@shared_task
def generate_performance_document(job_id, unker_id, year):
    job = ExportJob.objects.filter(id=job_id).first()

    try:
        job.status = "processing"
        job.save(update_fields=["status"])

        export_doc = export_dokumen_kinerja(unker_id, year)
        file_bytes = export_doc.getvalue()
        
        if file_bytes:
            filename=f"DOKUMEN_KINERJA_{year}.xlsx"
            job.file.save(filename, ContentFile(file_bytes), save=False)
            job.status = "success"
            job.save(update_fields=["status", "file"])

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.save(update_fields=["status", "error_message"])
        raise
