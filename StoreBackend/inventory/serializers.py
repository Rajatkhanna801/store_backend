from rest_framework import serializers
from .models import Category, Product, ProductImage
from cart.models import Cart, CartItem

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_added_to_cart = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "discounted_price", "effective_price", "quantity", "category", "images", "is_added_to_cart"]

    def get_is_added_to_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            # Get the user's cart
            cart = Cart.objects.filter(user=user).first()
            if cart:
                # Check if the product is already in the user's cart and is active
                cart_item = CartItem.objects.filter(cart=cart, product=obj, status=CartItem.Status.ACTIVE).first()
                return True if cart_item else False
        return False