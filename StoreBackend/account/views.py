from rest_framework import viewsets, generics, permissions, status, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db import models
from .models import Address
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    AddressSerializer,
    ChangePasswordSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomTokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from drf_spectacular.types import OpenApiTypes

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Custom response with tokens
        response_data = {
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
            },
            "access": access_token,
            "refresh": refresh_token
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
        

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
        # Enforce a single default address
        user_addresses = Address.objects.filter(user=self.request.user)
        is_first_address = not user_addresses.exclude(pk=addr.pk).exists()
        if is_first_address:
            if not addr.is_default:
                addr.is_default = True
                addr.save(update_fields=["is_default"])
        else:
            if addr.is_default:
                Address.objects.filter(user=self.request.user, is_default=True).exclude(pk=addr.pk).update(is_default=False)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        address = self.get_object()
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
        return Response({"detail": "Default address set."})

    def perform_update(self, serializer):
        previous: Address = self.get_object()
        was_default = previous.is_default
        addr: Address = serializer.save()
        # If toggled to default, unset others
        if addr.is_default:
            Address.objects.filter(user=self.request.user, is_default=True).exclude(pk=addr.pk).update(is_default=False)
        else:
            # If user tried to unset the only default, keep it default to ensure at least one default exists
            if was_default and not Address.objects.filter(user=self.request.user, is_default=True).exclude(pk=addr.pk).exists():
                addr.is_default = True
                addr.save(update_fields=["is_default"])


class EmailTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/accounts/login/
    Accepts: { "email_or_phone": "...", "password": "..." }
    Returns: refresh + access + user details
    
    Can login with either email or phone number.
    """
    serializer_class = CustomTokenObtainPairSerializer


class PhoneExistsView(generics.GenericAPIView):
    """
    GET /api/accounts/phone-exists/?phone=+911234567890
    Returns: { "exists": true/false }
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="phone_number",
                description="Alias for 'phone'",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        phone = request.query_params.get("phone_number")
        if not phone:
            return Response({"detail": "Missing 'phone_number' query parameter."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize phone number by removing +91 prefix for comparison
        if phone.startswith('+91'):
            normalized_phone = phone[3:]  # Remove first 3 characters (+91)
        else:
            normalized_phone = phone
        print(normalized_phone, 'normalized_phone')
        
        # Check if any user has this phone number (with or without +)
        exists = User.objects.filter(
            models.Q(phone_number=phone) | 
            models.Q(phone_number=f"+{normalized_phone}") |
            models.Q(phone_number=normalized_phone)
        ).exists()
        
        return Response({"exists": exists})


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'phone_number': {
                    'type': 'string',
                    'description': 'Phone number with country code',
                    'example': '+911234567890'
                },
                'otp_code': {
                    'type': 'string',
                    'description': 'OTP code',
                    'example': '123456'
                }
            },
            'required': ['phone_number', 'otp_code']
        }
    },
    responses={
        200: {
            'description': 'Login successful',
            'content': {
                'application/json': {
                    'example': {
                        'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1OTQxNzk4NCwiaWF0IjoxNzU4ODEzMTg0LCJqdGkiOiI5YjhlNjEyOThlYTA0MDBjOWFhMGYxNzgxOGNlNWYwNSIsInVzZXJfaWQiOiI1In0.w5_A4OsCrXBvNFXq2dhTBy4arPl3kPcB8BmsQtZmQak',
                        'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4ODE2Nzg0LCJpYXQiOjE3NTg4MTMxODQsImp0aSI6ImNhYmY1YzdkZmM2MjQxN2RhZTc1NWIwZGJhZjU3M2I5IiwidXNlcl9pZCI6IjUifQ.YHPhzak0x1Ot0EkZeurqsg-PRVco3ekSCiIcp-oy8v8',
                        'user': {
                            'id': 5,
                            'first_name': 'test',
                            'last_name': 'test',
                            'email': 'test1@yopmail.com',
                            'phone_number': '1234567898'
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request - missing phone_number',
            'content': {
                'application/json': {
                    'example': {
                        'detail': "'phone_number' is required."
                    }
                }
            }
        },
        404: {
            'description': 'User not found',
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'No user found with this phone number.'
                    }
                }
            }
        }
    }
)
class OTPLoginView(generics.CreateAPIView):
    """
    POST /api/accounts/login/otp/
    body: { "phone_number": "+911234567890", "otp_code": "123456" }

    """
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number")
        otp_code = request.data.get("otp_code")
        if not phone_number or not otp_code:
            return Response({"detail": "'phone_number' and 'otp_code' are required."}, status=status.HTTP_400_BAD_REQUEST)
        # Normalize phone number by removing +91 prefix for comparison
        if phone_number.startswith('+91'):
            normalized_phone = phone_number[3:]  # Remove first 3 characters (+91)
        else:
            normalized_phone = phone_number
        
        # Ensure user exists - check multiple phone number formats
        try:
            user = User.objects.filter(
                models.Q(phone_number=phone_number) | 
                models.Q(phone_number=f"+{normalized_phone}") |
                models.Q(phone_number=normalized_phone)
            ).first()
            
            if not user:
                raise User.DoesNotExist
        except User.DoesNotExist:
            return Response({"detail": "No user found with this phone number."}, status=status.HTTP_404_NOT_FOUND)

        # OTP verification is handled on the frontend. At this point, trust the request
        # and proceed to issue tokens if the user exists.

        # Issue tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "refresh": str(refresh),
            "access": str(access_token),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
            },
        }, status=status.HTTP_200_OK)

