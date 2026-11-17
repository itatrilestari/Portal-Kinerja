from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import  Q
from datetime import datetime
from apps.kinerja.serializers.performance_targets_serializers import PerformanceTargetRequestSerializer, PerformanceTargetsSerializer
from apps.kinerja.models import PerformanceTargets
from apps.api.utils import CustomPagination

class PerformanceTargetsRequestListCreateAPIView(generics.ListCreateAPIView):
    permission_class = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PerformanceTargetRequestSerializer
        return PerformanceTargetsSerializer

    def list(self, request, *args, **kwargs):
        query = self.get_queryset()
        paginated_queryset = self.paginate_queryset(query)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"user": request.user, "request": request})
        serializer.is_valid(raise_exception=True)
        instances = serializer.save() 
        response_serializer = self.get_serializer(instances)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        get_working_unit_id = self.request.query_params.get("working_unit_id")
        get_status = self.request.query_params.get("status")
        get_year = self.request.query_params.get("year")
        get_search = self.request.query_params.get("search")

        queryset = PerformanceTargets.objects.filter(is_delete=False)

        if get_working_unit_id:
            queryset = queryset.filter(working_unit__id=get_working_unit_id)

        if get_status:
            queryset = queryset.filter(status=get_status)

        if get_year:
            get_year = get_year
        else:
            get_year = datetime.now().year

        queryset = queryset.filter(year=get_year)

        if get_search:
            queryset = queryset.filter(Q(title__icontains=get_search) | Q(status=get_search))
        return queryset

class PerformanceTargetsRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PerformanceTargets.objects.filter(is_delete=False)
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == "PUT" or self.request.method == "PATCH":
            return PerformanceTargetRequestSerializer
        return PerformanceTargetsSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete=True
        instance.save()

        return Response({
            "message": "Delete Performance Targets Successfully",
            "data": {
                "id": str(instance.id)
            }
        }, status=status.HTTP_200_OK)
