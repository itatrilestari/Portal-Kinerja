import json, os
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.api.utils import CustomPagination
from apps.api.models import Profile, ExportJob
from apps.kinerja.serializers.performance_indicators_serializers import *
from apps.kinerja.utils import get_unker_ids_bfs
from apps.kinerja.tasks import *

# Create your views here.
class IndikatorKinerjaListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data, context={"user": user, "request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        result = []

        if get_unker:
            current = WorkingUnit.objects.filter(id=get_unker,is_delete=False).first()
            queryset = PerformanceIndicators.objects.filter(unker=parent, is_delete=False)

            if current:
                if current.level == "3" and current.level == "3":
                    is_approveable = False
                else:
                    is_approveable = True

                result.append({
                    "parent": {
                        "unit_kerja_id": current.id,
                        "unit_kerja": current.name,
                        "is_approveable": is_approveable,
                        "kode": current.code,
                        "level": current.level,
                        "unit_kerja_atasan_id": current.parent.id,
                        "unit_kerja_atasan": current.parent.name,
                        "unit_kerja_atasan_kode": current.parent.code,
                        "jumlah_ik": queryset.filter(is_delete=False).count(),
                        "jumlah_ik_digunakan": queryset.filter(state="Digunakan", is_delete=False).count(),
                        "jumlah_ik_tidak_digunakan": queryset.filter(state="Tidak Digunakan", is_delete=False).count()
                    }
                })

        result.extend(serializer.data)
        response = pagination.get_paginated_response(result)
        return response

    def get_queryset(self):
        get_unker = self.request.query_params.get("unker")
        get_year = self.request.query_params.get("year")
        search = self.request.query_params.get("search")
        get_status = self.request.query_params.get("status")
        get_approved_state = self.request.query_params.get("approved_state")
        get_priority = self.request.query_params.get("priority")

        queryset = PerformanceIndicators.objects.filter(is_delete=False)

        if get_unker:
            data_unker = WorkingUnit.objects.filter(id=get_unker, is_delete=False).first()
            if data_unker:
                queryset = queryset.filter(unker=data_unker)

        if get_year:
            queryset = queryset.filter(year=get_year)

        if search:
            queryset = queryset.filter(title__icontains=search)

        if get_status:
            queryset = queryset.filter(state=get_status)

        if get_approved_state:
            queryset = queryset.filter(approved_state=get_approved_state)

        if get_priority:
            if get_priority in ["true", "True", True]:
                get_priority = True
            elif get_priority in ["false", "False", False]:
                get_priority = False
            queryset = queryset.filter(is_priority=get_priority)

        return queryset.order_by('-updated_at')
    
class IndikatorOptionListAPIView(generics.ListAPIView):
    serializer_class = IndikatorKinerjaDetailSerializer
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
        return pagination.get_paginated_response(serializer.data)

    def get_queryset(self):
        get_type = self.request.query_params.get("type", None)
        get_year = self.request.query_params.get("year", None)
        get_unker = self.request.query_params.get("unker", None)

        queryset = PerformanceIndicators.objects.filter(is_delete=False, approved_state="Approved", state="Digunakan")
        if get_unker:
            data_unker = WorkingUnit.objects.filter(is_delete=False, id=get_unker).first()
            if data_unker:
                if get_type == "atasan" and get_year:
                    queryset = queryset.filter(cascading__overlap=[data_unker.unit_kerja_kode], year=get_year)
                if get_type == "tahun_sebelumnya" and get_year:
                    queryset = queryset.filter(unker=data_unker, year=get_year)

        return queryset.order_by('created_at')
    
class getIndikatorKinerjaSummaryListAPIView(generics.ListAPIView):
    serializer_class = IndikatorKinerjaSummarySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        get_unker = self.request.query_params.get("unker", None)
        search = self.request.query_params.get("search", None)
        get_year = self.request.query_params.get("year", None)

        queryset = WorkingUnit.objects.filter(is_delete=False)

        if get_unker:
            child = get_unker_ids_bfs(get_unker)
        else:
            data_unker_user = Profile.objects.get(nik=self.request.user.username).working_unit.id
            child = get_unker_ids_bfs(data_unker_user)

        queryset = queryset.filter(code__in=child)

        if search:
            queryset = queryset.filter(name__icontains=search)

        indikator_filter = Q(
            performanceindicators__is_delete=False
        )

        if get_year:
            indikator_filter &= Q(
                performanceindicators__year=get_year
            )

        queryset = queryset.annotate(
            jumlah_ik = Count(
                "performanceindicators",
                filter=indikator_filter
            ),
            jumlah_ik_digunakan = Count(
                "performanceindicators",
                filter=indikator_filter & 
                Q(performanceindicators__state="Digunakan")
            ),
            jumlah_ik_tidak_digunakan = Count(
                "performanceindicators",
                filter=indikator_filter & 
                Q(performanceindicators__state="Tidak Digunakan")
            ),
            on_progress=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="On Progress"),
            ),
            approved=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Approved"),
            ),
            rejected=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Rejected"),
            ),
            need_revision=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Revision Requested"),
            ),
            revision_approved=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Revision Approved"),
            ),
            revision_rejected=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Revision Rejected"),
            ),
            locked_count=Count(
                "performanceindicators",
                filter=indikator_filter &
                Q(performanceindicators__approved_state="Locked"),
            ),
        )

        return queryset.order_by('code')
    
class getIndikatorKinerjaDetailRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    serializer_class = IndikatorKinerjaDetailSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        state = request.data.get("state")
        instance.state = state
        instance.save()

        user = request.user

        message = f"[id: {instance.id}]"
        create_log(user, "Update", "Performance Indicator", message)
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

        user = request.user

        message = f"[id: {instance.id}]"
        create_log(user, "Delete", "Performance Indicator", message)

        return Response({
            "message": "Berhasil hapus Indikator Kinerja",
            "data": {
                "id": str(instance.id)
            }
        }, status=status.HTTP_200_OK)
    
class getIndikatorKinerjaDetailUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    serializer_class = IndikatorKinerjaDetailUpdateSerializer
    lookup_field = 'id'

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
        instance = serializer.save()
        return Response(IndikatorKinerjaDetailSerializer(instance).data,status=status.HTTP_200_OK)

class getIndikatorKinerjaCascadingListAPIView(generics.ListAPIView):
    serializer_class = IndikatorKinerjaDetailSerializer
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

        result = []
        get_reference_indicator = self.request.query_params.get("reference_indicator")
        queryset = PerformanceIndicators.objects.filter(is_delete=False)
        if get_reference_indicator:
            data = queryset.filter(id=get_reference_indicator)
            if data:
                for d in data:
                    result.append({
                        "parent": {
                            "unit_kerja": d.unker.name,
                            "indikator_kinerja_nama": d.title,
                            "target": d.target,
                            "jenis_cascading": d.cascading_method
                        }
                    })

        result.extend(serializer.data)
        response = pagination.get_paginated_response(result)
        return response

    def get_queryset(self):
        get_reference_indicator = self.request.query_params.get("reference_indicator")
        get_year = self.request.query_params.get("year")
        search = self.request.query_params.get("search")

        queryset = PerformanceIndicators.objects.filter(is_delete=False)

        if get_reference_indicator:
            parent = queryset.filter(id=get_reference_indicator)
            if parent:
                queryset = queryset.filter(reference_indicator__in=parent)

        if get_year:
            queryset = queryset.filter(year=get_year)

        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset
    
class DownloadMatriksTargetRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker", None)
        get_year = request.data.get("year", None)

        job = ExportJob.objects.create(
            job_type="indicator_matrix_target",
            status="pending",
            requested_by=request.user,
        )

        result = generate_matrix_target.delay(job.id, get_unker, get_year)

        print(result)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class DownloadRincianIndikatorRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker", [])
        get_year = request.data.get("year", None)
        get_unker_nama = request.data.get("unker_nama", None)

        job = ExportJob.objects.create(
            job_type="indicator_rincian_indikator",
            status="pending",
            requested_by=request.user,
        )

        generate_rincian_indikator.delay(job.id, get_unker, get_year, get_unker_nama)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class DownloadRincianTargetRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker", [])
        get_year = request.data.get("year")
        get_unker_nama = request.data.get("unker_nama")

        job = ExportJob.objects.create(
            job_type="indicator_rincian_target",
            status="pending",
            requested_by=request.user,
        )

        generate_rincian_target.delay(str(job.id), get_unker, get_year, get_unker_nama)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )
    
class DownloadPenetapanIndikatorRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker")
        get_year = request.data.get("year")
        get_unker_nama = request.data.get("unker_nama")

        job = ExportJob.objects.create(
            job_type="indicator_penetapan_indikator",
            status="pending",
            requested_by=request.user,
        )

        generate_penetapan_indicator.delay(str(job.id), get_unker, get_year, get_unker_nama)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )

class DownloadCapaianIndikatorRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_unker = request.data.get("unker")
        get_year = request.data.get("year")
        get_tw = request.data.get("tw")
        get_unker_nama = request.data.get("unker_nama")

        job = ExportJob.objects.create(
            job_type="indicator_penetapan_indikator",
            status="pending",
            requested_by=request.user,
        )

        generate_capaian_indicator.delay(str(job.id), get_unker, get_year, get_tw, get_unker_nama)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )

class ActionPerformanceIndicatorCreateAPIView(generics.CreateAPIView):
    serializer_class = ActionPerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"user": request.user, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
class getDialogHistoryListAPIView(generics.ListAPIView):
    serializer_class = getDialogHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        get_indicator_id = self.request.query_params.get("indicator_id")

        queryset = PerformanceIndicators.objects.filter(is_delete=False)

        if get_indicator_id:
            queryset = queryset.filter(id=get_indicator_id)

        return queryset
    
class getDialogHistoryLogRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    queryset = Log.objects.filter(is_delete=False)

class getNeedApprovalListAPIView(generics.ListAPIView):
    serializer_class = IndikatorKinerjaDetailSerializer
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
        return pagination.get_paginated_response(serializer.data)
    
    def get_queryset(self):
        get_year = self.request.query_params.get("year")
        search = self.request.query_params.get("search")
        get_status = self.request.query_params.get("status")
        get_unker = self.request.query_params.get("unker")

        users = self.request.user.username

        get_unker_user = Profile.objects.get(nik=users).working_unit

        queryset = PerformanceIndicators.objects.filter(is_delete=False, approved_state__in=["On Progress", "Revision Requested"])

        if get_year:
            queryset = queryset.filter(year=get_year)

        if search:
            queryset = queryset.filter(title__icontains=search)

        if get_status:
            queryset = queryset.filter(state=get_status)


        if get_unker_user.level == "1":
            if get_unker:
                queryset = queryset.filter(unker_id__id=get_unker)
        else:
            queryset = queryset.exclude(
                unker_id__code=get_unker_user.code
            )
            if get_unker:
                queryset = queryset.filter(unker_id__id=get_unker)

        return queryset.order_by('-created_at')

class RequestRevisionPerformanceIndicatorUpdateAPIView(generics.UpdateAPIView):
    serializer_class = RequestRevisionPerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={
                "user": request.user,
                "request": request
            }
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    
class EditRevisionPerformanceIndicatorUpdateAPIView(generics.UpdateAPIView):
    serializer_class = EditRevisionPerformanceIndicatorSerializer
    permission_classes = [IsAuthenticated]
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={
                "user": request.user,
                "request": request
            }
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)

# # class GetNomorAPIView(APIView):
# #     permission_classes = [IsAuthenticated]

# #     def get(self, request):
# #         unit_kerja_kode = request.query_params.get("unit_kerja_kode")
# #         category = request.query_params.get("category")

# #         nomor = Nomor.objects.filter(
# #             unit_kerja__unit_kerja_kode=unit_kerja_kode,
# #             category=category,
# #             is_delete=False
# #         ).first()

# #         serializer = NomorSerializer(nomor)

# #         return Response(serializer.data)
    
# class GetNomorAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         unit_kerja_kode = request.query_params.get("unit_kerja_kode")
#         category = request.query_params.get("category")
#         year = request.query_params.get("year", datetime.now().year)

#         unit_kerja = UnitKerja.objects.filter(
#             unit_kerja_kode=unit_kerja_kode
#         ).first()

#         if not unit_kerja:
#             return Response(
#                 {"detail": "Unit kerja tidak ditemukan"},
#                 status=400
#             )

#         code = get_next_available_number(
#             unit_kerja=unit_kerja,
#             category=category,
#             year=year,
#         )

#         return Response({
#             "code": code
#         })

# class NomorCreateAPIView(generics.CreateAPIView):
#     queryset = Nomor.objects.all()
#     serializer_class = NomorSerializer

#     def create(self, request, *args, **kwargs):

#         unit_kerja_code = request.data.get("unit_kerja")
#         category = request.data.get("category")
#         code = request.data.get("code")

#         if not unit_kerja_code:
#             return Response({
#                 "message": "Unit kerja wajib diisi"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         if not category:
#             return Response({
#                 "message": "Category wajib diisi"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         if not code:
#             return Response({
#                 "message": "Code wajib diisi"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             unit_kerja = UnitKerja.objects.get(
#                 unit_kerja_kode=unit_kerja_code
#             )
#         except UnitKerja.DoesNotExist:
#             return Response({
#                 "message": "Unit kerja tidak ditemukan"
#             }, status=status.HTTP_404_NOT_FOUND)

#         year = datetime.now().year

#         nomor_obj, created = Nomor.objects.get_or_create(
#             unit_kerja=unit_kerja,
#             category=category,
#             year=year,
#             defaults={
#                 "code": code,
#                 "last_number": 1
#             }
#         )

#         # jika sudah ada, update code saja
#         if not created:

#             if nomor_obj.code != code:
#                 nomor_obj.code = code
#                 nomor_obj.save()

#         generated_number = (
#             f"{str(nomor_obj.last_number).zfill(2)}"
#         )

#         serializer = self.get_serializer(nomor_obj)

#         return Response({
#             "message": "Nomor berhasil dibuat",
#             "generated_number": generated_number,
#             "data": serializer.data
#         }, status=status.HTTP_201_CREATED)

# class NomorUpdateAPIView(generics.UpdateAPIView):
#     queryset = Nomor.objects.all()
#     serializer_class = NomorSerializer
#     lookup_field = "id"

#     def update(self, request, *args, **kwargs):

#         nomor_obj = self.get_object()

#         code = request.data.get("code")
#         last_number = request.data.get("last_number")

#         if code is not None:
#             nomor_obj.code = code

#         if last_number is not None:
#             nomor_obj.last_number = last_number

#         nomor_obj.save()

#         serializer = self.get_serializer(nomor_obj)

#         return Response({
#             "message": "Nomor berhasil diupdate",
#             "data": serializer.data
#         }, status=status.HTTP_200_OK)

class PerformanceIndicatorUpdateNotification(generics.UpdateAPIView):
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        extra = instance.extra_attributes or {}
        extra["notification"] = request.data.get("notification")
        instance.extra_attributes = extra
        instance.save(update_fields=["extra_attributes"])

        return Response(
            {"message": "Update Status notifikasi berhasil dilakukan"},
            status=status.HTTP_200_OK,
        )

class PerformanceIndicatorUpdatePrioritas(generics.UpdateAPIView):
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        is_priority = request.data.get("is_priority")

        if is_priority is None:
            return Response(
                {"message": "Field is_priority wajib diisi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.is_priority = is_priority
        instance.save(update_fields=["is_priority"])

        user = request.user

        message = f"[id: {instance.id}]"

        create_log(user, "Update", "Performance Indicator", message)

        return Response(
            {"message": "Update Prioritas berhasil dilakukan"},
            status=status.HTTP_200_OK,
        )