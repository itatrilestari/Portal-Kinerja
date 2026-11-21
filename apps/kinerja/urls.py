from django.urls import path, include
from apps.kinerja.views import (
    performance_targets_views,
    performance_indicators_views,
    export_tasks_views,
    performance_document_views,
    recommendation_views
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

    path('dokumen-kinerja/', include([
        path('', performance_document_views.PerformanceDocumentSummaryListAPIView.as_view(), name='dokumen-kinerja-list'),
        path('download/', performance_document_views.PerformanceSummaryDownloadListAPIView.as_view(), name='dokumen-kinerja-list-download'),
        path('create/', performance_document_views.PerformanceDocumentCreateAPIView.as_view(), name='dokumen-kinerja-create'),
        path('detail/', performance_document_views.PerformanceDocumentListAPIView.as_view(), name='dokumen-kinerja-detail'),
        path('<uuid:id>/', performance_document_views.PerformanceDocumentRetrieveUpdateDestroyAPIView.as_view(), name='dokumen-kinerja'),
        path('download-attachment/', performance_document_views.DownloadAttachmentListAPIView.as_view(), name='download-attachment'),
    ])),

    path('rekomendasi/', include([
        path('', recommendation_views.RecommendationListAPIView.as_view(), name='list-rekomendasi'),
        path('download/excel/', recommendation_views.DownloadRekomendasiExcelRetrieveAPIView.as_view(), name='download-rekomendasi-excel'),
        path('download/pdf/', recommendation_views.DownloadRekomendasiPdfRetrieveAPIView.as_view(), name='download-rekomendasi-pdf'),
        path('summary/', recommendation_views.RecommendationSummaryListAPIView.as_view(), name='rekomendasi-summary'),
        path('summary/download/', recommendation_views.DownloadSummaryRetrieveAPIView.as_view(), name='rekomendasi-summary-download'),
        path('create/', recommendation_views.RecommendationCreateAPIView.as_view(), name='rekomendasi-create'),
        path('create/rekomendasi/', recommendation_views.RecommendationCreateRekomendasiAPIView.as_view(), name='rekomendasi-create'),
        path('<uuid:id>/', recommendation_views.RecommendationRetrieveUpdateDestroyAPIView.as_view(), name='rekomendasi-detail'),
        path('tindak-lanjut/', recommendation_views.TindakLanjutList.as_view(), name='list-tindak-lanjut'),
        path('action/', recommendation_views.ActionResolutionCreateAPIView.as_view(), name='action-tindak-lanjut'),
        path('need-verification/', recommendation_views.getNeedVerificationListAPIView.as_view(), name='action-tindak-lanjut'),
        path('dialog-history/', recommendation_views.getDialogHistoryResolutionListAPIView.as_view(), name='action-tindak-lanjut'),
        path('<uuid:id>/delete/tindak-lanjut/', recommendation_views.ResolutionDestroyAPIView.as_view(), name='delete-tindak-lanjut'),
        path('tindak-lanjut/<uuid:id>/update/notification/', recommendation_views.TindakLanjutUpdateNotification.as_view(), name='update-notification-tindak-lanjut'),
    ])),

    path('export/<uuid:id>/status/', export_tasks_views.ExportJobStatusAPIView.as_view(), name='export-status'),
]