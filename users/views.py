from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .permissions import IsAdminRole
from .serializers import (
    RegisterSerializer, UserSerializer,
    CustomTokenObtainPairSerializer, AdminCreateUserSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AdminCreateUserView(generics.CreateAPIView):
    """POST /api/auth/admin/create-user/ — admin-only, can set any role."""
    queryset = CustomUser.objects.all()
    serializer_class = AdminCreateUserSerializer
    permission_classes = [IsAdminRole]


class AdminUserListView(generics.ListAPIView):
    """GET /api/auth/admin/users/ — admin-only, lists everyone, filterable by ?role="""
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by('username')
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs