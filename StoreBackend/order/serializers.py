from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Order, OrderItem, Checkout, CheckoutItem, StoreSettings
from inventory.serializers import ProductSerializer
from account.serializers import AddressSerializer
from decimal import Decimal

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
    subtotal = serializers.SerializerMethodField()
    delivery_charge = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    minimum_order_amount = serializers.SerializerMethodField()

    def get_subtotal(self, obj):
        return sum(item.price_at_checkout * item.quantity for item in obj.items.all())

    def get_delivery_charge(self, obj):
        store_settings = StoreSettings.objects.first()
        return store_settings.delivery_charge if store_settings else Decimal('0.00')

    def get_total_amount(self, obj):
        return self.get_subtotal(obj) + self.get_delivery_charge(obj)

    def get_minimum_order_amount(self, obj):
        store_settings = StoreSettings.objects.first()
        return store_settings.minimum_order_amount if store_settings else Decimal('0.00')
    
    class Meta:
        model = Checkout
        fields = ["id", "user", "shipping_address", "items", "subtotal", "delivery_charge", "total_amount", "minimum_order_amount", "expires_at", "is_active", "created_at"]

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
    subtotal = serializers.SerializerMethodField()
    delivery_charge = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    payment_qr_data = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    def get_subtotal(self, obj):
        return obj.subtotal()

    def get_delivery_charge(self, obj):
        return obj.get_delivery_charge()

    def get_total_amount(self, obj):
        return obj.total_amount()

    class Meta:
        model = Order
        fields = [
            "id", "user", "shipping_address", "status", "payment_status", 
            "payment_qr_data", "notes", "items", 
            "subtotal", "delivery_charge", "total_amount", "created_at", "updated_at"
        ]
        read_only_fields = [
            "user", "shipping_address", "created_at", "updated_at", 
            "subtotal", "delivery_charge", "total_amount", "payment_qr_data", "payment_status"
        ]

class OrderSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for order summary with payment info"""
    subtotal = serializers.SerializerMethodField()
    delivery_charge = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    payment_qr_data = serializers.CharField(read_only=True)
    payment_status = serializers.CharField(read_only=True)

    def get_subtotal(self, obj):
        return obj.subtotal()

    def get_delivery_charge(self, obj):
        return obj.get_delivery_charge()
    
    def get_total_amount(self, obj):
        return obj.total_amount()

    class Meta:
        model = Order
        fields = ["id", "subtotal", "delivery_charge", "total_amount", "payment_qr_data", "payment_status", "status", "created_at"]
        read_only_fields = ["subtotal", "delivery_charge", "total_amount", "payment_qr_data", "payment_status"]
