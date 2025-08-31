from rest_framework import serializers
from .models import Cart, CartItem
from inventory.serializers import ProductSerializer

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

    class Meta:
        model = Cart
        fields = ["id", "items", "created_at", "updated_at"]
