from rest_framework import viewsets, permissions, status, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Order, OrderItem, Checkout, CheckoutItem, StoreSettings
from cart.models import Cart, CartItem
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderItemWriteSerializer,
    OrderSummarySerializer, CheckoutSerializer, CheckoutCreateSerializer
)
from account.models import Address
from inventory.models import Product
from .utils import generate_upi_payment_data, validate_inventory_for_order

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for consistent API responses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

class CheckoutViewSet(viewsets.ViewSet):
    """ViewSet for managing temporary checkouts"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckoutSerializer
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        summary="Create checkout from cart items",
        description="Create a temporary checkout that reserves items for configurable time",
        request=CheckoutCreateSerializer,
        responses={
            201: CheckoutSerializer,
            400: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "errors": {"type": "object"}
                }
            }
        },
        examples=[
            OpenApiExample(
                "Create checkout",
                value={
                    "cart_item_ids": [1, 2, 3],
                    "shipping_address_id": 1
                },
                description="Example request to checkout specific cart items"
            )
        ]
    )
    @action(detail=False, methods=["post"])
    def create_checkout(self, request):
        """Create temporary checkout with selected cart items"""
        serializer = CheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        cart_item_ids = serializer.validated_data["cart_item_ids"]
        shipping_address_id = serializer.validated_data["shipping_address_id"]
        
        try:
            with transaction.atomic():
                # Validate shipping address
                shipping_address = get_object_or_404(
                    Address, id=shipping_address_id, user=user
                )
                
                # Get cart items and validate inventory
                cart_items = CartItem.objects.filter(
                    id__in=cart_item_ids,
                    cart__user=user,
                    status=CartItem.Status.ACTIVE
                ).select_related("product")
                
                if not cart_items.exists():
                    return Response(
                        {"detail": "No valid cart items found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check the minimum order amount
                store_settings = StoreSettings.objects.first()
                total_amount = sum(item.product.effective_price * item.quantity for item in cart_items)
                if total_amount < store_settings.minimum_order_amount:
                    return Response(
                        {"detail": f"Minimum order amount is {store_settings.minimum_order_amount}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate inventory using utility function
                is_valid, inventory_errors = validate_inventory_for_order(cart_items)
                if not is_valid:
                    return Response(
                        {"detail": "Insufficient inventory", "errors": inventory_errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create checkout (automatically sets configurable expiration)
                checkout = Checkout.objects.create(
                    user=user,
                    shipping_address=shipping_address
                )
                
                # Create checkout items and temporarily reduce inventory
                for cart_item in cart_items:
                    CheckoutItem.objects.create(
                        checkout=checkout,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price_at_checkout=cart_item.product.effective_price,
                    )
                    
                    # Temporarily reduce inventory (will be restored if checkout expires)
                    cart_item.product.quantity -= cart_item.quantity
                    cart_item.product.save()
                
                # Remove items from cart (they're now in checkout)
                cart_items.delete()
                
                response_serializer = CheckoutSerializer(checkout)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"detail": f"Failed to create checkout: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Get checkout details",
        description="Get details of a specific checkout",
        responses={200: CheckoutSerializer}
    )
    @action(detail=True, methods=["get"])
    def get_checkout(self, request, pk=None):
        """Get checkout details"""
        checkout = get_object_or_404(Checkout, id=pk, user=request.user)
        
        # Check if checkout has expired
        if checkout.is_expired():
            checkout.mark_expired()
            return Response(
                {"detail": "Checkout has expired. Items returned to inventory."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CheckoutSerializer(checkout)
        return Response(serializer.data)

    @extend_schema(
        summary="Cancel checkout",
        description="Cancel checkout and return items to inventory",
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
    )
    @action(detail=True, methods=["post"])
    def cancel_checkout(self, request, pk=None):
        """Cancel checkout and return items to inventory"""
        checkout = get_object_or_404(Checkout, id=pk, user=request.user)
        
        if not checkout.is_active:
            return Response(
                {"detail": "Checkout is already cancelled or expired"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        checkout.mark_expired()
        return Response({"detail": "Checkout cancelled. Items returned to inventory."})

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "items__product", "shipping_address"
        )

    @extend_schema(
        summary="List user orders",
        description="Get all orders for the authenticated user",
        responses={200: OrderSerializer(many=True)}
    )
    def list(self, request):
        return super().list(request)

    @extend_schema(
        summary="Get order details",
        description="Get detailed information about a specific order",
        responses={200: OrderSerializer}
    )
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

    @extend_schema(
        summary="Create order from checkout",
        description="Convert a checkout to a permanent order",
        request=OrderCreateSerializer,
        responses={
            201: OrderSerializer,
            400: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"}
                }
            }
        },
        examples=[
            OpenApiExample(
                "Create order from checkout",
                value={
                    "checkout_id": 1,
                    "notes": "Please deliver in the morning"
                },
                description="Example request to convert checkout to order"
            )
        ]
    )
    @action(detail=False, methods=["post"])
    def create_order(self, request):
        """Convert checkout to permanent order"""
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        checkout_id = serializer.validated_data["checkout_id"]
        notes = serializer.validated_data.get("notes", "")
        
        try:
            with transaction.atomic():
                # Get checkout and validate it belongs to user
                checkout = get_object_or_404(Checkout, id=checkout_id, user=user)
                
                # Check if checkout is still active and not expired
                if not checkout.is_active:
                    return Response(
                        {"detail": "Checkout is no longer active"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if checkout.is_expired():
                    checkout.mark_expired()
                    return Response(
                        {"detail": "Checkout has expired. Items returned to inventory."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create order from checkout
                order = Order.objects.create(
                    user=user,
                    shipping_address=checkout.shipping_address,
                    notes=notes
                )
                
                # Create order items from checkout items
                for checkout_item in checkout.items.all():
                    # Ensure we have a valid price for the order item
                    price_at_purchase = checkout_item.price_at_checkout
                    if price_at_purchase is None:
                        # Fallback to product's current effective price
                        if hasattr(checkout_item.product, 'effective_price'):
                            price_at_purchase = checkout_item.product.effective_price
                        elif hasattr(checkout_item.product, 'price'):
                            price_at_purchase = checkout_item.product.price
                        else:
                            price_at_purchase = 0
                    
                    OrderItem.objects.create(
                        order=order,
                        product=checkout_item.product,
                        quantity=checkout_item.quantity,
                        price_at_purchase=price_at_purchase,
                    )
                    # Inventory is already reduced, no need to reduce again
                
                # Mark checkout as inactive and clear checkout items
                checkout.is_active = False
                checkout.save()
                
                # Clear all checkout items since they're now in the order
                checkout.items.all().delete()
                
                # Generate UPI payment data
                order.payment_qr_data = generate_upi_payment_data(
                    order.total_amount(), order.id
                )
                order.save()
                
                response_serializer = OrderSerializer(order)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"detail": f"Failed to create order: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Checkout all cart items (legacy)",
        description="Create a new order from all active cart items (legacy method)",
        request=None,
        responses={
            201: OrderSerializer,
            400: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"}
                }
            }
        }
    )
    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """Legacy checkout method - orders all active cart items directly"""
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        items = cart.items.filter(status=CartItem.Status.ACTIVE)

        if not items.exists():
            return Response({"detail": "Cart is empty"}, status=400)

        # For now, shipping address from user default
        address = user.addresses.filter(is_default=True).first()
        if not address:
            return Response({"detail": "No default address set"}, status=400)

        try:
            with transaction.atomic():
                # Validate inventory using utility function
                is_valid, inventory_errors = validate_inventory_for_order(items)
                if not is_valid:
                    return Response(
                        {"detail": "Insufficient inventory", "errors": inventory_errors},
                        status=400
                    )

                order = Order.objects.create(user=user, shipping_address=address)

                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price_at_purchase=item.product.effective_price,
                    )
                    # Update inventory
                    item.product.quantity -= item.quantity
                    item.product.save()
                
                # Clear cart
                items.delete()
                
                # Generate UPI payment data
                order.payment_qr_data = generate_upi_payment_data(
                    order.total_amount(), order.id
                )
                order.save()

                serializer = OrderSerializer(order)
                return Response(serializer.data, status=201)
                
        except Exception as e:
            return Response(
                {"detail": f"Failed to create order: {str(e)}"},
                status=400
            )

    @extend_schema(
        summary="Get order summary",
        description="Get order summary with payment information",
        responses={200: OrderSummarySerializer}
    )
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get order summary with payment info for display"""
        order = get_object_or_404(Order, id=pk, user=request.user)
        serializer = OrderSummarySerializer(order)
        return Response(serializer.data)
