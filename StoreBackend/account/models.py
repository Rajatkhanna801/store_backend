from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractUser):
    """
    Custom user using username + email.
    If you prefer email-only auth, switch to AbstractBaseUser later.
    """
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(r"^\+?\d{7,15}$", "Enter a valid phone number.")],
        help_text="E.g. +919999999999",
    )

    REQUIRED_FIELDS = ["email"]  # when using createsuperuser if username is kept

    def __str__(self):
        return self.get_full_name() or self.username

class Address(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=100, blank=True, help_text="Home, Work, etc.")
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    pincode = models.CharField(max_length=12)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city", "pincode"]),
        ]

    def __str__(self):
        return f"{self.label or 'Address'} • {self.city} • {self.pincode}"
