from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    RegisterView,
    ProfileView,
    AddressViewSet,
    ChangePasswordView,
    EmailTokenObtainPairView,
)

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),  # email login
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ProfileView.as_view(), name="profile"),
    path("password/change/", ChangePasswordView.as_view(), name="password_change"),
]

urlpatterns += router.urls
