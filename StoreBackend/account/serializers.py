from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "phone_number"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "password"]

    def validate_email(self, value):
        """
        Validate that the email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        """
        Validate that the phone number is unique if provided.
        """
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def validate(self, attrs):
        """
        Ensure at least one of email or phone_number is provided.
        """
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")
        
        if not email and not phone_number:
            raise serializers.ValidationError(
                "Either email or phone number must be provided."
            )
        
        return attrs

    def create(self, validated_data):
        # Use email as username if available, otherwise use phone number
        username = validated_data.get("email") or validated_data.get("phone_number")
        
        user = User.objects.create_user(
            username=username,
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone_number=validated_data.get("phone_number", ""),
            password=validated_data["password"],
        )
        return user


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for JWT login using email or phone number.
    """

    email_or_phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            self.fields.pop("username")

    def validate_email_or_phone(self, value):
        """
        Validate that the provided value is either a valid email or phone number.
        """
        from django.core.validators import validate_email, RegexValidator
        from django.core.exceptions import ValidationError
        
        # Check if it's an email
        try:
            validate_email(value)
            return value
        except ValidationError:
            pass
        
        # Check if it's a phone number
        phone_validator = RegexValidator(r"^\+?\d{7,15}$", "Enter a valid phone number.")
        try:
            phone_validator(value)
            return value
        except ValidationError:
            raise serializers.ValidationError(
                "Enter a valid email address or phone number."
            )

    def validate(self, attrs):
        email_or_phone = attrs["email_or_phone"]
        
        # Determine if it's email or phone and find the user
        user = None
        
        # Check if it's an email
        if "@" in email_or_phone:
            try:
                user = User.objects.get(email=email_or_phone)
                attrs["username"] = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "No active account found with this email address."
                )
        else:
            # It's a phone number
            try:
                user = User.objects.get(phone_number=email_or_phone)
                attrs["username"] = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "No active account found with this phone number."
                )

        # Perform default validation (creates tokens & sets self.user)
        data = super().validate(attrs)

        # At this point, self.user exists ✅
        user = self.user

        # Add user details in response
        data.update({
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
            }
        })

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
