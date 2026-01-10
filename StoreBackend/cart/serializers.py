from rest_framework import serializers
from .models import Cart, CartItem
from order.models import StoreSettings
from inventory.serializers import ProductSerializer
from account.serializers import AddressSerializer

class CartItemWriteSerializer(serializers.Serializer):
    """Serializer for creating/updating cart items"""
    product_id = serializers.IntegerField(
        help_text="ID of the product to add to cart",
        min_value=1
    )
    quantity = serializers.IntegerField(
        help_text="Quantity of the product",
        min_value=1,
        default=1
    )
    status = serializers.ChoiceField(
        choices=CartItem.Status.choices,
        default=CartItem.Status.ACTIVE,
        help_text="Status of the cart item"
    )

class CartItemReadSerializer(serializers.ModelSerializer):
    """Serializer for reading cart items"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "status", "created_at", "updated_at"]

class CartItemSerializer(serializers.ModelSerializer):
    """Legacy serializer for backward compatibility"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "status"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    user_address = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()
    delivery_charge = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "user_address",
            "delivery_charge",
            "totals",
            "created_at",
            "updated_at",
        ]

    def get_user_address(self, obj):
        try:
            default_address = obj.user.addresses.filter(is_default=True).last()
            return AddressSerializer(default_address).data if default_address else None
        except obj.user.addresses.model.DoesNotExist:
            return {}

    def get_delivery_charge(self, obj):
        settings = StoreSettings.objects.order_by("-id").first()
        return settings.delivery_charge if settings else 0

    def get_totals(self, obj):
        """
        Expected obj.subtotal_details() example:
        {
            "subtotal": 1200.00,
            "tax": 0.00,
            "total": 1200.00
        }
        """
        totals = obj.subtotal_details()

        settings = StoreSettings.objects.order_by("-id").first()
        delivery_charge = settings.delivery_charge if settings else 0

        totals["delivery_charge"] = delivery_charge
        totals["grand_total"] = totals.get("total", 0) + delivery_charge

        return totals


