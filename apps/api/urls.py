from django.urls import path, include
from api.views import RegisterCreateAPIView, ProfileRetrieveAPIView, LoginAPIView, TitleListCreateAPIView

urlpatterns = [
    path('register/', RegisterCreateAPIView.as_view(), name='register'),
    path('profile/me/', ProfileRetrieveAPIView.as_view(), name='user'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('kinerja/', include('apps.kinerja.urls')),

    path("admintools/", include([
        path("title/", include([
            path('', TitleListCreateAPIView.as_view(), name='list-create-title'),
        ])),
    ])),
]