from rest_framework import viewsets, permissions, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, CartItemWriteSerializer, CartItemReadSerializer
from inventory.models import Product

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for consistent API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @extend_schema(
        summary="List cart items",
        description="Get all items in the user's cart along with the default user address (or empty dict if no default address)",
        responses={200: CartSerializer},
        examples=[
            OpenApiExample(
                "Cart with items and default address",
                value={
                    "id": 1,
                    "items": [
                        {
                            "id": 1,
                            "product": {
                                "id": 1,
                                "name": "Sample Product",
                                "price": "99.99"
                            },
                            "quantity": 2,
                            "status": "active",
                            "created_at": "2025-01-13T10:00:00Z",
                            "updated_at": "2025-01-13T10:00:00Z"
                        }
                    ],
                    "user_address": {
                        "id": 1,
                        "street_address": "123 Main St",
                        "city": "New York",
                        "state": "NY",
                        "postal_code": "10001",
                        "country": "USA",
                        "is_default": True,
                        "created_at": "2025-01-13T10:00:00Z",
                        "updated_at": "2025-01-13T10:00:00Z"
                    },
                    "created_at": "2025-01-13T10:00:00Z",
                    "updated_at": "2025-01-13T10:00:00Z"
                },
                description="Example response showing cart items and default address"
            ),
            OpenApiExample(
                "Cart with items and no default address",
                value={
                    "id": 1,
                    "items": [
                        {
                            "id": 1,
                            "product": {
                                "id": 1,
                                "name": "Sample Product",
                                "price": "99.99"
                            },
                            "quantity": 2,
                            "status": "active",
                            "created_at": "2025-01-13T10:00:00Z",
                            "updated_at": "2025-01-13T10:00:00Z"
                        }
                    ],
                    "user_addresses": {},
                    "created_at": "2025-01-13T10:00:00Z",
                    "updated_at": "2025-01-13T10:00:00Z"
                },
                description="Example response when user has no default address"
            )
        ]
    )
    def list(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Add item to cart",
        description="Add a product to the user's cart",
        request=CartItemWriteSerializer,
        responses={200: CartItemReadSerializer},
        examples=[
            OpenApiExample(
                "Add product to cart",
                value={
                    "product_id": 1,
                    "quantity": 2,
                    "status": "active"
                },
                description="Example request to add 2 units of product ID 1 to cart"
            )
        ]
    )
    @action(detail=False, methods=["post"])
    def add(self, request):
        """
        Add a product to the cart.
        
        Required fields:
        - product_id: ID of the product to add
        - quantity: Quantity (default: 1)
        - status: Status of the item (default: active)
        """
        cart = self.get_cart(request.user)
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product = get_object_or_404(Product, id=serializer.validated_data["product_id"])
        item, created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            status=serializer.validated_data.get("status", CartItem.Status.ACTIVE),
            defaults={"quantity": serializer.validated_data["quantity"]},
        )
        return Response(CartItemReadSerializer(item).data)

    @extend_schema(
        summary="Update cart item",
        description="Update quantity, product, or status of a specific cart item by its ID. If quantity becomes 0, the item is automatically removed from cart.",
        request=CartItemWriteSerializer,
        responses={200: CartItemReadSerializer},
        parameters=[
            OpenApiParameter(
                name="item_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the cart item to update (this is the cart item ID, not the cart ID)"
            )
        ],
        examples=[
            OpenApiExample(
                "Update cart item quantity",
                value={
                    "quantity": 3
                },
                description="Example: Update quantity of cart item ID 5 to 3 units"
            ),
            OpenApiExample(
                "Update cart item status",
                value={
                    "status": "saved"
                },
                description="Example: Mark cart item ID 5 as saved for later"
            )
        ]
    )
    @action(detail=False, methods=["patch"], url_path="items/(?P<item_id>[^/.]+)/update")
    def update_item(self, request, item_id):
        cart = self.get_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        serializer = CartItemWriteSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Check if quantity is being set to 0 (remove item)
        if "quantity" in serializer.validated_data:
            new_quantity = serializer.validated_data["quantity"]
            if new_quantity <= 0:
                # Remove the item if quantity is 0 or negative
                item.delete()
                return Response({
                    "detail": "Item removed from cart (quantity set to 0)",
                    "removed": True
                })
            else:
                item.quantity = new_quantity
        
        # Update other fields
        if "product_id" in serializer.validated_data:
            product = get_object_or_404(Product, id=serializer.validated_data["product_id"])
            item.product = product
        if "status" in serializer.validated_data:
            item.status = serializer.validated_data["status"]
        
        item.save()
        return Response(CartItemReadSerializer(item).data)

    @extend_schema(
        summary="Remove cart item",
        description="Remove a specific cart item from the user's cart by its ID",
        responses={200: dict},
        parameters=[
            OpenApiParameter(
                name="item_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the cart item to remove (this is the cart item ID, not the cart ID)"
            )
        ]
    )
    @action(detail=False, methods=["delete"])
    def remove_item(self, request, item_id):
        """
        Remove a specific cart item from the user's cart.
        
        This endpoint removes an existing cart item by its ID.
        The cart item ID is different from the cart ID. Each user has one cart,
        but can have multiple cart items within that cart.
        """
        cart = self.get_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response({"detail": "Item removed"})
