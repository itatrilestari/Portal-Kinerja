from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.api.utils import CustomPagination
from apps.api.models import *
from apps.kinerja.models import *
from apps.kinerja.utils import get_unker_ids_bfs
from apps.kinerja.tasks import generate_recommendation_summary, generate_recommendation_excel, generate_recommendation_pdf
from apps.kinerja.serializers.recommendation_serializers import *

class RecommendationSummaryListAPIView(generics.ListAPIView):
    serializer_class = RecommendationSummarySerializer
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
        if get_year:
            serializer = self.get_serializer(paginated_queryset, many=True, context={"year":get_year})
        else:
            serializer = self.get_serializer(paginated_queryset, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def get_queryset(self):
        get_unker = self.request.query_params.get("unker", None)
        search = self.request.query_params.get("search", None)
        get_year = self.request.query_params.get("year", None)

        queryset = WorkingUnit.objects.filter(is_delete=False)

        if get_unker:
            child = get_unker_ids_bfs(get_unker)
        else:
            data_unker_user = Profile.objects.get(nip=self.request.user.username).working_unit
            child = get_unker_ids_bfs(data_unker_user)

        queryset = queryset.filter(code__in=child)

        if search:
            queryset = queryset.filter(unit_kerja_nama__icontains=search)

        recommendation_filter = Q(
            recommendation__is_delete=False
        )

        if get_year:
            recommendation_filter &= Q(recommendation__year=get_year)

        queryset = queryset.annotate(
            jumlah_rekomendasi=Count(
                "recommendation__id",
                filter=(
                    recommendation_filter &
                    Q(recommendation__is_delete=False)
                ),
                distinct=True,
            ),
            jumlah_tindak_lanjut = Count(
                "recommendation__resolution",
                filter= recommendation_filter &
                Q (recommendation__resolution__is_delete=False)
            ),
            jumlah_tuntas = Count(
                "recommendation__resolution",
                filter= recommendation_filter &
                Q (recommendation__resolution__is_delete=False, recommendation__resolution__status="Tuntas")
            ),
            jumlah_on_progress = Count(
                "recommendation__resolution",
                filter= recommendation_filter &
                Q (recommendation__resolution__is_delete=False, recommendation__resolution__status="On Progress")
            ),
        )

        return queryset
    
class RecommendationListAPIView(generics.ListAPIView):
    serializer_class = RecommendationSerializer
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
        serializer = self.get_serializer(paginated_queryset, many=True)

        get_unker = self.request.query_params.get("unker")
        get_year = self.request.query_params.get("year")

        result = []

        if get_unker:
            unker = WorkingUnit.objects.filter(
                id=get_unker,
                is_delete=False
            ).first()
                
            result.append({
                "card": {
                    "unit_kerja": unker.name,
                    "kode": unker.code,
                    "tahun": get_year
                }
            })

        result.extend(serializer.data)
        response = pagination.get_paginated_response(result)
        return response
    
    def get_queryset(self):
        get_unker = self.request.query_params.get("unker", None)
        search = self.request.query_params.get("search", None)
        get_year = self.request.query_params.get("year", None)

        queryset = Recommendation.objects.filter(is_delete=False)

        if get_unker:
            queryset = queryset.filter(unker__id=get_unker)

        if get_year:
            queryset = queryset.filter(year=get_year)

        if search:
            queryset = queryset.filter(instruction__icontains=search)

        return queryset.order_by('-updated_at')
    
class RecommendationCreateAPIView(generics.CreateAPIView):
    serializer_class = RecommendationCreateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"user": request.user, "request": request})
        serializer.is_valid(raise_exception=True)
        instances = serializer.save() 
        response_serializer = self.get_serializer(instances)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class RecommendationCreateRekomendasiAPIView(generics.CreateAPIView):
    serializer_class = RecommendationCreateRekomendasiSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"user": request.user, "request": request})
        serializer.is_valid(raise_exception=True)
        instances = serializer.save() 
        response_serializer = self.get_serializer(instances)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class RecommendationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recommendation.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecommendationAllSerializer
        return RecommendationDetailSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
            context={"user": request.user, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            "message": "Berhasil update rekomendasi",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete = True
        instance.save()

        message = f"[id: {instance.id}]"
        create_log(request.user, "Delete", "Recommendation", message)
        return Response({
            "message": "Berhasil hapus rekomendasi",
            "data": {
                "id": str(instance.id)
            }
        }, status=status.HTTP_200_OK)

class TindakLanjutList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = TindakLanjutListSerializer

    def get_queryset(self):
        get_id_rekomendasi = self.request.query_params.get("id_rekomendasi", None)
        get_status = self.request.query_params.get("status", None)
        queryset = Resolution.objects.filter(is_delete=False)

        if get_id_rekomendasi:
            queryset = queryset.filter(recommendation_id__id=get_id_rekomendasi)

        if get_status:
            if get_status == "Need Verificated":
                queryset = queryset.filter(verification_state="Need Verificated", status="Tuntas")
            elif get_status == "Verificated":
                queryset = queryset.filter(verification_state="Verificated", status="Tuntas")
            else:
                queryset = queryset.filter(status=get_status)
        return queryset
    
class ActionResolutionCreateAPIView(generics.CreateAPIView):
    serializer_class = ActionResolutionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"user": request.user, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
class getNeedVerificationListAPIView(generics.ListAPIView):
    serializer_class = TindakLanjutListSerializer
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
        serializer = self.get_serializer(paginated_queryset, many=True)

        result = {}
        for obj, item in zip(paginated_queryset, serializer.data):
            recommendation = obj.recommendation

            if recommendation.id not in result:
                result[recommendation.id] = {
                    "unit_kerja": recommendation.unker.name,
                    "tahun": recommendation.year,
                    "rekomendasi": recommendation.instruction,
                    "tindak_lanjut": []
                }

            result[recommendation.id]["tindak_lanjut"].append(item)

        return pagination.get_paginated_response(
            list(result.values())
        )
    
    def get_queryset(self):
        get_year = self.request.query_params.get("year")
        search = self.request.query_params.get("search")
        get_status = self.request.query_params.get("status")
        get_nip = self.request.query_params.get("nip")

        users = get_nip if get_nip else self.request.user.username

        queryset = Resolution.objects.filter(is_delete=False, recommendation_id__approver__contains=[users], verification_state="Need Verificated")

        if get_year:
            queryset = queryset.filter(created_at__year=get_year)

        if search:
            queryset = queryset.filter(action__icontains=search)

        if get_status:
            queryset = queryset.filter(status=get_status)

        return queryset.order_by('-updated_at')
    
class getDialogHistoryResolutionListAPIView(generics.ListAPIView):
    serializer_class = getDialogHistoryResolutionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        get_id_tindak_lanjut = self.request.query_params.get("id_tindak_lanjut")

        if get_id_tindak_lanjut:
            queryset = Resolution.objects.filter(id=get_id_tindak_lanjut,is_delete=False)

        return queryset
    
class ResolutionDestroyAPIView(generics.DestroyAPIView):
    queryset = Resolution.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete = True
        instance.save()

        message = f"[id: {instance.id}]"
        create_log(request.user, "Delete", "Resolution", message)
        return Response({
            "message": "Berhasil hapus tindak lanjut",
            "data": {
                "id": str(instance.id)
            }
        }, status=status.HTTP_200_OK)
    
class DownloadSummaryRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker")
        get_year = request.data.get("year")

        job = ExportJob.objects.create(
            job_type="recommendation_summary",
            status="pending",
            requested_by=request.user,
        )

        generate_recommendation_summary.delay(str(job.id), get_unker, get_year)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class DownloadRekomendasiExcelRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker")
        get_year = request.data.get("year")

        job = ExportJob.objects.create(
            job_type="recommendation_excel",
            status="pending",
            requested_by=request.user,
        )

        generate_recommendation_excel.delay(str(job.id), get_unker, get_year)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class DownloadRekomendasiPdfRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker")
        get_year = request.data.get("year")

        job = ExportJob.objects.create(
            job_type="recommendation_pdf",
            status="pending",
            requested_by=request.user,
        )

        generate_recommendation_pdf.delay(str(job.id), get_unker, get_year)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class TindakLanjutUpdateNotification(generics.UpdateAPIView):
    queryset = Resolution.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        extra = instance.extra_attributes or {}
        extra["notification"] = request.data.get("notification")
        instance.extra_attributes = extra
        instance.save(update_fields=["extra_attributes"])

        return Response(
            {"message": "Status notifikasi berhasil dilakukan"},
            status=status.HTTP_200_OK,
        )