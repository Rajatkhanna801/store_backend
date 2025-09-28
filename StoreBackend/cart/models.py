from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from inventory.models import Product
from decimal import Decimal

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Cart(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"Cart({self.user})"

    def subtotal(self):
        """Calculate cart subtotal with proper decimal handling"""
        try:
            items = self.items.filter(status=CartItem.Status.ACTIVE).select_related("product")
            total = Decimal('0.00')
            
            for item in items:
                if item.product:
                    # Get the effective price, fallback to regular price
                    if hasattr(item.product, 'effective_price'):
                        price = item.product.effective_price
                    elif hasattr(item.product, 'price'):
                        price = item.product.price
                    else:
                        continue
                    
                    if price is not None:
                        # Convert to Decimal for proper calculation
                        item_price = Decimal(str(price))
                        item_total = item_price * item.quantity
                        total += item_total
            
            return total
        except Exception:
            # Return 0 if there's any calculation error
            return Decimal('0.00')

    def subtotal_details(self):
        """Calculate totals: actual, total (effective), discount"""
        items = self.items.filter(status=CartItem.Status.ACTIVE).select_related("product")
        actual_price = Decimal("0.00")
        total_amount = Decimal("0.00")

        for item in items:
            if not item.product:
                continue

            # original (non-discounted) price
            if item.product.price is not None:
                actual_price += Decimal(str(item.product.price)) * item.quantity

            # effective price (discounted if available)
            effective = item.product.effective_price
            if effective is not None:
                total_amount += Decimal(str(effective)) * item.quantity

        discount_price = actual_price - total_amount
        return {
            "actual_price": actual_price,
            "total_amount": total_amount,
            "discount_price": discount_price
        }


class CartItem(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SAVED = "saved_for_later", "Saved for Later"

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        indexes = [
            models.Index(fields=["cart", "status"]),
        ]
        # Allow same product twice only if status differs (Amazon-like)
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product", "status"],
                name="unique_cart_product_per_status",
            )
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity} ({self.status})"
