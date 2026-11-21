from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from apps.api.models import ExportJob
from apps.api.utils import CustomPagination
from apps.kinerja.serializers.performance_documents_serializers import *
from apps.kinerja.models import PerformanceDocument
from django.http import FileResponse
from apps.kinerja.tasks import generate_performance_document
from apps.kinerja.utils import get_unker_ids_bfs

class PerformanceDocumentSummaryListAPIView(generics.ListAPIView):
    serializer_class = PerformanceDocumentListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def list(self, request, *args, **kwargs):
        get_limit = request.query_params.get("limit")
        queryset = self.get_queryset()
        if get_limit:
            limit = get_limit
        else:
            limit = 999
        pagination = CustomPagination()
        paginated_queryset = pagination.paginate_queryset(queryset, request)

        get_year = self.request.query_params.get("year", None)
        print("d", get_year)
        if get_year:
            print("ini")
            serializer = self.get_serializer(paginated_queryset, many=True, context={"year":get_year})
        else:
            print("ini2")
            serializer = self.get_serializer(paginated_queryset, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def get_queryset(self):
        get_unker = self.request.query_params.get("unker", None)
        search = self.request.query_params.get("search", None)
        get_year = self.request.query_params.get("year", None)

        child = None
        queryset = WorkingUnit.objects.filter(is_delete=False)

        if get_unker:
            child = get_unker_ids_bfs(get_unker)

        queryset = queryset.filter(code__in=child)

        if search:
            queryset = queryset.filter(name__icontains=search)

        filters = Q(
            performancedocument__is_delete=False,
            performancedocument__year=get_year,
        )

        queryset = queryset.annotate(
            pohon_kinerja = Count(
                "performancedocument",
                filter=filters &
                Q(performancedocument__category="Pohon Kinerja")
            ),
            renstrai = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Renstra")
            ),
            renja = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Renja")
            ),
            pk = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="PK")
            ),
            sk_indikator_kinerja = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="SK Indikator Kinerja")
            ),
            manual_indikator_kinerja = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Manual Indikator Kinerja")
            ),
            matrix_cascading_mph = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Matrix Cascading / MPH")
            ),
            rencana_aksi = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Rencana Aksi")
            ),
            rincian_target_indikator = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Rincian Target Indikator")
            ),
            laporan_kinerja_tw1 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Laporan Kinerja TW I")
            ),
            laporan_kinerja_tw2 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Laporan Kinerja TW II")
            ),
            laporan_kinerja_tw3 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Laporan Kinerja TW III")
            ),
            laporan_kinerja_tw4 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Laporan Kinerja TW IV")
            ),
            evaluasi_kinerja_tw1 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Evaluasi Kinerja TW I")
            ),
            evaluasi_kinerja_tw2 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Evaluasi Kinerja TW II")
            ),
            evaluasi_kinerja_tw3 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Evaluasi Kinerja TW III")
            ),
            evaluasi_kinerja_tw4 = Count(
                "performancedocument",
                filter=filters & 
                Q (performancedocument__category="Evaluasi Kinerja TW IV")
            ),
        )

        return queryset
    
class PerformanceDocumentCreateAPIView(generics.CreateAPIView):
    serializer_class = PerformanceDocumentCreateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"user": request.user, "request": request})
        serializer.is_valid(raise_exception=True)
        instances = serializer.save() 
        response_serializer = self.get_serializer(instances)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
class PerformanceDocumentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformanceDocument.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    serializer_class = PerformanceDocumentSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        state = request.data.get("status")
        instance.state = state
        instance.save()

        message = f"[id: {instance.id}]"
        create_log(request.user, "Update", "Performance Document", message)
        return Response({
            "message": "Berhasil update status",
            "data": {
                "id": str(instance.id),
                "state": instance.state
            }
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete = True
        instance.save()

        message = f"[id: {instance.id}]"
        create_log(request.user, "Delete", "Performance Document",message)
        return Response({
            "message": "Berhasil hapus dokumen kinerja",
            "data": {
                "id": str(instance.id)
            }
        }, status=status.HTTP_200_OK)
    
class PerformanceDocumentListAPIView(generics.ListAPIView):
    serializer_class = PerformanceDocumentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def list(self, request, *args, **kwargs):
        get_limit = request.query_params.get("limit")
        queryset = self.get_queryset()
        if get_limit:
            limit = get_limit
        else:
            limit = 999
        pagination = CustomPagination()
        paginate_queryset = pagination.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginate_queryset, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def get_queryset(self):
        get_unker = self.request.query_params.get("unker", None)
        get_category = self.request.query_params.get("category", None)
        get_year = self.request.query_params.get("year", None)
        search = self.request.query_params.get("search", None)

        queryset = PerformanceDocument.objects.filter(is_delete=False)

        if get_unker:
            data_unker = WorkingUnit.objects.get(id=get_unker)
            if data_unker:
                queryset = queryset.filter(unker_id=data_unker)

        if get_category:
            queryset = queryset.filter(category = get_category)

        if get_year:
            queryset = queryset.filter(year = get_year)

        if search:
            queryset = queryset.filter(Q(category__icontains=search) | Q(notes__icontains=search))

        return queryset.order_by('-updated_at')
    
class PerformanceSummaryDownloadListAPIView(generics.ListAPIView):
    serializer_class = PerformanceDocumentListSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        get_unker = self.request.query_params.get("unker")
        get_year = self.request.query_params.get("year")

        # create job
        job = ExportJob.objects.create(
            job_type="dokumen_kinerja_summary",
            status="pending",
            requested_by=request.user,
        )
        generate_performance_document.delay(str(job.id), get_unker, get_year)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    

class DownloadAttachmentListAPIView(generics.ListAPIView):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        get_id_attachment = request.query_params.get("id_attachment", None)
        if get_id_attachment:
            attachment = Attachment.objects.get(id=get_id_attachment)
            if attachment:
                response = FileResponse(
                    attachment.file.open('rb'),
                    as_attachment=True,
                    filename=attachment.filename
                )
            else:
                response = None
        return response