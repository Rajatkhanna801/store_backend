from rest_framework import viewsets, generics, permissions, status, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .models import Address
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    AddressSerializer,
    ChangePasswordSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

User = get_user_model()

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for consistent API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/accounts/me/  -> current user profile
    PATCH/PUT -> update profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    POST /api/accounts/password/change/
    body: { "old_password": "...", "new_password": "..." }
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-is_default", "-created_at")

    def perform_create(self, serializer):
        addr = serializer.save(user=self.request.user)
        # If it's the first address, make it default automatically
        if not Address.objects.filter(user=self.request.user).exclude(pk=addr.pk).exists():
            addr.is_default = True
            addr.save(update_fields=["is_default"])

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        address = self.get_object()
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
        return Response({"detail": "Default address set."})


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/accounts/login/
    Accepts: { "email": "...", "password": "..." }
    Returns: refresh + access + user details
    """
    serializer_class = CustomTokenObtainPairSerializer

