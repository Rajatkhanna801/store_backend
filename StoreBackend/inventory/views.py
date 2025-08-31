from rest_framework import viewsets, filters, permissions, pagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

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
