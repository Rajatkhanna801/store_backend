from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import OrderViewSet, CheckoutViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")
router.register("checkouts", CheckoutViewSet, basename="checkout")

urlpatterns = router.urls
