from rest_framework import serializers
from core.models import SiteSettings, ContactMessage


class SiteSettingsSerializer(serializers.ModelSerializer):
    display_address = serializers.CharField(read_only=True)
    display_footer_text = serializers.CharField(read_only=True)
    display_shipping_message = serializers.CharField(read_only=True)

    class Meta:
        model = SiteSettings
        fields = (
            "company_name",
            "phone",
            "whatsapp",
            "email",
            "address",
            "address_ar",
            "display_address",
            "facebook",
            "instagram",
            "tiktok",
            "footer_text",
            "footer_text_ar",
            "display_footer_text",
            "shipping_message",
            "shipping_message_ar",
            "display_shipping_message",
            "currency",
        )


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ("id", "name", "phone", "email", "subject", "message", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_phone(self, value):
        cleaned = value.replace(" ", "")
        if len(cleaned) < 10 or not cleaned.lstrip("+").isdigit():
            raise serializers.ValidationError("Enter a valid phone number (at least 10 digits).")
        return cleaned

