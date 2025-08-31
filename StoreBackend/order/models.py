from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from account.models import Address
from inventory.models import Product

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Checkout(TimeStampedModel):
    """Temporary checkout model to hold items for configurable time"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="checkouts")
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="checkouts")
    expires_at = models.DateTimeField(help_text="Checkout expires after configured time")
    is_active = models.BooleanField(default=True, help_text="Whether this checkout is still valid")
    
    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Get expiry time from settings (default: 2 hours)
            expiry_hours = getattr(settings, 'CHECKOUT_EXPIRY_HOURS', 2)
            self.expires_at = timezone.now() + timedelta(hours=expiry_hours)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if checkout has expired"""
        return timezone.now() > self.expires_at
    
    def time_until_expiry(self):
        """Get time remaining until expiry"""
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - timezone.now()
    
    def mark_expired(self):
        """Mark checkout as expired and return items to inventory"""
        if self.is_active:
            self.is_active = False
            self.save()
            
            # Return items to inventory
            for item in self.items.all():
                item.product.quantity += item.quantity
                item.product.save()
    
    def __str__(self):
        expiry_hours = getattr(settings, 'CHECKOUT_EXPIRY_HOURS', 2)
        return f"Checkout #{self.id} by {self.user} (expires in {expiry_hours}h)"

class CheckoutItem(TimeStampedModel):
    """Items in temporary checkout"""
    checkout = models.ForeignKey(Checkout, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="checkout_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_checkout = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        indexes = [
            models.Index(fields=["checkout"]),
        ]
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity} in checkout"

class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True
    )

    # For QR-based manual payment
    payment_qr_data = models.CharField(
        max_length=512,
        blank=True,
        help_text="UPI/deeplink data embedded in the QR; generate at order creation.",
    )
    payment_qr_image = models.ImageField(
        upload_to="payment_qr/",
        blank=True,
        null=True,
        help_text="Optional pre-generated QR image stored on server.",
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def total_price(self):
        """Calculate total price for this order item"""
        if self.price_at_purchase is None:
            return 0
        return self.price_at_purchase * self.quantity
