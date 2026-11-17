from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.api.serializers import RegisterSerializer, UserSerializer, LoginSerializer, ProfileSerializer, TitleSerializer
from apps.api.models import Title
from apps.api.utils import CustomPagination

class RegisterCreateAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)

class ProfileRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile_set.first()

class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer

class TitleListCreateAPIView(generics.ListCreateAPIView):
    permission_class = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = TitleSerializer
    queryset = Title.objects.filter(is_delete=False)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"user": request.user, "request": request})
        serializer.is_valid(raise_exception=True)
        instances = serializer.save() 
        response_serializer = self.get_serializer(instances)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)