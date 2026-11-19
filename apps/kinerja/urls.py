from django.urls import path, include
from apps.kinerja.views import (
    performance_targets_views,
    performance_indicators_views,
    export_tasks_views
)

urlpatterns = [
    path("performance-targets/", include([
        path('', performance_targets_views.PerformanceTargetsRequestListCreateAPIView.as_view(), name='list-create-performance-targets'),
        path('<uuid:id>/', performance_targets_views.PerformanceTargetsRetrieveUpdateDestroyAPIView.as_view(), name='detail-update-delete-performance-targets'),
    ])),
    path('indikator-kinerja/', include([
        path('option/', performance_indicators_views.IndikatorOptionListAPIView.as_view(), name="option-indikator"),
        path('', performance_indicators_views.IndikatorKinerjaListCreateAPIView.as_view(), name='indikator-kinerja'),
        path('summary/', performance_indicators_views.getIndikatorKinerjaSummaryListAPIView.as_view(), name='indikator-kinerja-summary'),
        path('<uuid:id>/', performance_indicators_views.getIndikatorKinerjaDetailRetrieveUpdateDestroyAPIView.as_view(), name='indikator-kinerja-detail'),
        path('<uuid:id>/draft/', performance_indicators_views.getIndikatorKinerjaDetailUpdate.as_view(), name='indikator-kinerja-edit-draft'),
        path('cascading/', performance_indicators_views.getIndikatorKinerjaCascadingListAPIView.as_view(), name='indikator-kinerja-cascading'),
        path("download/", include([
            path('matriks-target/', performance_indicators_views.DownloadMatriksTargetRetrieveAPIView.as_view(), name='indikator-kinerja-download-matriks-target'),
            path('rincian-indikator/', performance_indicators_views.DownloadRincianIndikatorRetrieveAPIView.as_view(), name='indikator-kinerja-download-rincian-indikator'),
            path('rincian-target/', performance_indicators_views.DownloadRincianTargetRetrieveAPIView.as_view(), name='indikator-kinerja-download-rincian-target'),
            path('penetapan-indikator/', performance_indicators_views.DownloadPenetapanIndikatorRetrieveAPIView.as_view(), name='indikator-kinerja-download-penetapan-indikator'),
            path('capaian-indikator/', performance_indicators_views.DownloadCapaianIndikatorRetrieveAPIView.as_view(), name='indikator-kinerja-download-capaian-indikator'),
        ])),
        path('action/', performance_indicators_views.ActionPerformanceIndicatorCreateAPIView.as_view(), name='indikator-kinerja-action'),
        path('dialog-history/', performance_indicators_views.getDialogHistoryListAPIView.as_view(), name='indikator-kinerja-dialog-history'),
        path('dialog-history/log/<uuid:id>/', performance_indicators_views.getDialogHistoryLogRetrieveAPIView.as_view(), name='indikator-kinerja-dialog-history-log'),
        path('need-approval/', performance_indicators_views.getNeedApprovalListAPIView.as_view(), name='indikator-kinerja-need-approval'),
        path('<uuid:id>/request-revision/', performance_indicators_views.RequestRevisionPerformanceIndicatorUpdateAPIView.as_view(), name='indikator-kinerja-request-revision'),
        path('<uuid:id>/edit-revision/', performance_indicators_views.EditRevisionPerformanceIndicatorUpdateAPIView.as_view(), name='indikator-kinerja-edit-revision'),
        path('<uuid:id>/update-notification/', performance_indicators_views.PerformanceIndicatorUpdateNotification.as_view(), name='indikator-kinerja-update-notification'),
        path('<uuid:id>/update-prioritas/', performance_indicators_views.PerformanceIndicatorUpdatePrioritas.as_view(), name='indikator-kinerja-update-prioritas'),
    ])),

    #Export Status
    path('export/<uuid:id>/status/', export_tasks_views.ExportJobStatusAPIView.as_view(), name='export-status'),
]