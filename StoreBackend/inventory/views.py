from rest_framework import viewsets, filters, permissions, pagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from .models import Category, Product, Banner
from .serializers import CategorySerializer, ProductSerializer, BannerSerializer

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for consistent API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # Public access for categories
    pagination_class = StandardResultsSetPagination

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().select_related("category").prefetch_related("images")
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["category"]  # ?category=1
    ordering_fields = ["price", "created_at", "name"]  # ?ordering=price or -price
    search_fields = ["name", "description"]  # ?search=galaxy
    permission_classes = [permissions.AllowAny]  # Public access for products

    def get_serializer_context(self):
        """
        Add the user to the serializer context so it can be accessed in the serializer.
        """
        context = super().get_serializer_context()
        context['request'] = self.request  # Add the request to the context
        return context


# Example of a protected view that requires authentication
class UserFavoriteViewSet(viewsets.ModelViewSet):
    """
    Example of how to use JWT authentication in other apps.
    This view requires a valid JWT token to access.
    """
    serializer_class = CategorySerializer  # Using CategorySerializer as example
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        # This will automatically use the authenticated user from JWT token
        user = self.request.user
        # Example: return user-specific data
        return Category.objects.all()  # Placeholder - replace with actual user-specific logic


class BannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        now = timezone.now()
        return Banner.objects.filter(
            is_active=True
        ).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now)
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=now)
        ).order_by("-priority", "-created_at")
