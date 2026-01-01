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
    icon = models.ImageField(
        upload_to="category_icons/",
        blank=True,
        null=True,
        help_text="Upload a small icon for this category"
    )

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


class Banner(TimeStampedModel):
    class LinkType(models.TextChoices):
        PRODUCT = 'product', 'Product'
        CATEGORY = 'category', 'Category'
        EXTERNAL = 'external', 'External URL'
        SCREEN = 'screen', 'App Screen'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="banners/")
    link_type = models.CharField(
        max_length=20,
        choices=LinkType.choices,
        default=LinkType.PRODUCT
    )
    link_value = models.CharField(
        max_length=255,
        blank=True,
        help_text="Product ID, Category ID, external URL, or screen name"
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Higher priority banners appear first"
    )

    class Meta:
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return self.title
