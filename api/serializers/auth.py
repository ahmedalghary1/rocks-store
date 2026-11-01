from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Address

User = get_user_model()


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff", "date_joined")
        read_only_fields = ("id", "is_staff", "date_joined")

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    email = serializers.EmailField(required=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password", "password_confirm", "tokens")
        read_only_fields = ("id", "tokens")

    def validate_username(self, value):
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        user_candidate = User(
            username=attrs.get("username"),
            email=attrs.get("email"),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        validate_password(attrs["password"], user=user_candidate)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

    @extend_schema_field(TokenPairSerializer)
    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        validate_password(attrs["new_password"], user=self.context["request"].user)
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id",
            "label",
            "recipient_name",
            "phone",
            "governorate",
            "city",
            "address_line",
            "is_default",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default", False):
            Address.objects.filter(user=user).update(is_default=False)
        return Address.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default", False):
            Address.objects.filter(user=user).exclude(pk=instance.pk).update(is_default=False)
        return super().update(instance, validated_data)
