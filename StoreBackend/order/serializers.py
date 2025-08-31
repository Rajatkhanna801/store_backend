from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Order, OrderItem, Checkout, CheckoutItem
from inventory.serializers import ProductSerializer
from account.serializers import AddressSerializer

class CheckoutItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = CheckoutItem
        fields = ["id", "product", "quantity", "price_at_checkout"]

class CheckoutSerializer(serializers.ModelSerializer):
    items = CheckoutItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Checkout
        fields = ["id", "user", "shipping_address", "items", "expires_at", "is_active", "created_at"]

class CheckoutCreateSerializer(serializers.Serializer):
    """Serializer for creating checkout with selected cart items"""
    cart_item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        help_text="List of cart item IDs to checkout",
        min_length=1
    )
    shipping_address_id = serializers.IntegerField(
        help_text="ID of the shipping address to use for checkout",
        min_value=1
    )

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_total_price(self, obj):
        return obj.total_price

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price_at_purchase", "total_price"]
        read_only_fields = ["total_price"]

class OrderItemWriteSerializer(serializers.Serializer):
    """Serializer for creating order items from cart items"""
    cart_item_id = serializers.IntegerField(
        help_text="ID of the cart item to order",
        min_value=1
    )
    quantity = serializers.IntegerField(
        help_text="Quantity to order (defaults to cart item quantity if not specified)",
        min_value=1,
        required=False
    )

class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders from checkout"""
    checkout_id = serializers.IntegerField(
        help_text="ID of the checkout to convert to order",
        min_value=1
    )
    notes = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Optional notes for the order"
    )

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    notes = serializers.CharField(read_only=True)
    total_amount = serializers.SerializerMethodField()
    payment_qr_data = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)  # Admin only

    def get_total_amount(self, obj):
        return obj.total_amount()

    class Meta:
        model = Order
        fields = [
            "id", "user", "shipping_address", "status", "payment_status", 
            "payment_qr_data", "notes", "items", 
            "total_amount", "created_at", "updated_at"
        ]
        read_only_fields = [
            "user", "shipping_address", "created_at", "updated_at", 
            "total_amount", "payment_qr_data", "payment_status"
        ]

class OrderSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for order summary with payment info"""
    total_amount = serializers.SerializerMethodField()
    payment_qr_data = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)  # Admin only
    
    def get_total_amount(self, obj):
        return obj.total_amount()

    class Meta:
        model = Order
        fields = ["id", "total_amount", "payment_qr_data", "payment_status", "status", "created_at"]
        read_only_fields = ["total_amount", "payment_qr_data", "payment_status"]
