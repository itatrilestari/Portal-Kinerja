from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from apps.api.utils import CustomPagination
from apps.kinerja.models import PerformanceIndicators, PerformanceTargets
from apps.kinerja.serializers.performance_tree_serializers import *
from django.http import HttpResponse
from django.db.models import Q

class PohonKinerjaListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PohonKinerjaListSerializer
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
        get_unker = self.request.query_params.get("unker", None)
        get_year = self.request.query_params.get("year", None)
        get_search = self.request.query_params.get("search", None)

        queryset = PerformanceIndicators.objects.filter(is_delete=False)

        if get_unker:
            queryset = queryset.filter(unker__id=get_unker)

        if get_year:
            queryset = queryset.filter(created_at__year=get_year)

        if get_search:
            queryset = queryset.filter(
                Q(status__icontains=get_search) | Q(title__icontains=get_search)
            )
        return queryset

class PohonKinerjaCascadingListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PohonKinerjaListSerializer
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
        get_reference_indicator = self.kwargs.get("id")
        get_unker = self.request.query_params.get("unker", None)
        get_year = self.request.query_params.get("year", None)
        get_search = self.request.query_params.get("search", None)

        queryset = PerformanceIndicators.objects.filter(is_delete=False)

        if get_reference_indicator:
            parent = queryset.filter(id=get_reference_indicator)
            if parent:
                queryset = queryset.filter(reference_indicator__in=parent)

        if get_unker:
            queryset = queryset.filter(unker__id=get_unker)

        if get_year:
            queryset = queryset.filter(year=get_year)

        if get_search:
            queryset = queryset.filter(
                Q(status__icontains=get_search) | Q(title__icontains=get_search) |
                Q(performance_targets__status__icontains=get_search) | Q(performance_targets__title__icontains=get_search)
            )

        print(queryset)
        return queryset

class PohonKinerjaDetailRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = PohonKinerjaDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = PerformanceIndicators.objects.filter(is_delete=False)
    lookup_field = "id"

class PohonKinerjaMindMapRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = PohonKinerjaMindmapSerializer
    permission_classes = [IsAuthenticated]
    queryset = PerformanceTargets.objects.filter(is_delete=False)
    lookup_field = "id"