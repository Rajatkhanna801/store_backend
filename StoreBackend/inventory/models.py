from django.db import models
from django.core.validators import MinValueValidator

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discounted_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField(default=0)  # current stock

    class Meta:
        indexes = [
            models.Index(fields=["category", "name"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(price__gte=0), name="product_price_gte_0"),
            models.CheckConstraint(
                check=models.Q(discounted_price__gte=0) | models.Q(discounted_price__isnull=True),
                name="product_discounted_price_gte_0_or_null",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        return self.discounted_price if self.discounted_price is not None else self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Image for {self.product.name}"
