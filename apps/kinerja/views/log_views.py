from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.api.utils import CustomPagination
from apps.api.models import Log, ExportJob
from apps.kinerja.serializers.log_serializers import LogSerializer
from django.db.models import Q
from apps.kinerja.tasks import generate_log_activity

class LogActivityListAPIView(generics.ListAPIView):
    pagination_class = CustomPagination
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        query = self.get_queryset()
        paginated_queryset = self.paginate_queryset(query)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        search = self.request.query_params.get("search", None)
        queryset = Log.objects.filter(is_delete=False)

        if search:
            queryset = queryset.filter(Q(action__icontains=search) | Q(profile__nama__icontains=search))
        return queryset.order_by("-created_at")

class DownloadLogActivityRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        get_year = request.data.get("year")

        job = ExportJob.objects.create(
            job_type="indicator_penetapan_indikator",
            status="pending",
            requested_by=request.user,
        )

        generate_log_activity.delay(str(job.id), get_year)

        return Response(
            {"job_id": str(job.id), "status": job.status},
            status=status.HTTP_202_ACCEPTED,
        )