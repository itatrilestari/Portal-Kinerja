from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.api.models import ExportJob

class ExportJobStatusAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    queryset = ExportJob.objects.all()

    def retrieve(self, request, *args, **kwargs):
        job = self.get_object()

        data = {
            "job_id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
        }

        if job.status == "success" and job.file:
            data["download_url"] = request.build_absolute_uri(job.file.url)
        elif job.status == "failed":
            data["error_message"] = job.error_message

        return Response(data, status=status.HTTP_200_OK)