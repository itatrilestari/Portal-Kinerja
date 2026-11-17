from django.urls import path, include
from apps.kinerja.views import (
    performance_targets_views
)

urlpatterns = [
    path("performance-targets/", include([
        path('', performance_targets_views.PerformanceTargetsRequestListCreateAPIView.as_view(), name='list-create-performance-targets'),
        path('<uuid:id>/', performance_targets_views.PerformanceTargetsRetrieveUpdateDestroyAPIView.as_view(), name='detail-update-delete-performance-targets'),
    ]))
]