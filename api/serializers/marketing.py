from rest_framework import serializers
from marketing.models import Banner, Subscriber


class BannerSerializer(serializers.ModelSerializer):
    display_title = serializers.CharField(read_only=True)
    display_subtitle = serializers.CharField(read_only=True)
    display_button_text = serializers.CharField(read_only=True)

    class Meta:
        model = Banner
        fields = (
            "id",
            "title",
            "title_ar",
            "display_title",
            "subtitle",
            "subtitle_ar",
            "display_subtitle",
            "image",
            "mobile_image",
            "link",
            "button_text",
            "button_text_ar",
            "display_button_text",
            "location",
            "sort_order",
        )


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ("email",)

    def create(self, validated_data):
        email = validated_data["email"].strip().lower()
        subscriber, _ = Subscriber.objects.update_or_create(
            email=email,
            defaults={"is_active": True},
        )
        return subscriber

