import hashlib
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ContactMessage, SiteSettings
from api.serializers.core import ContactMessageSerializer, SiteSettingsSerializer


def _notify_contact(message_id):
    try:
        item = ContactMessage.objects.get(pk=message_id)
        if settings.ORDER_NOTIFICATION_EMAIL:
            send_mail(
                f"Contact message: {item.subject}",
                f"Name: {item.name}\nPhone: {item.phone}\nEmail: {item.email}\n\n{item.message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.ORDER_NOTIFICATION_EMAIL],
                fail_silently=True,
            )
    except Exception:
        pass


class SiteSettingsView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Storefront & Settings"],
        description="Retrieve site branding, contact info, WhatsApp number, social links, and messages",
        responses=SiteSettingsSerializer,
    )
    def get(self, request):
        site_settings = SiteSettings.objects.first()
        if not site_settings:
            site_settings = SiteSettings.objects.create()
        return Response(SiteSettingsSerializer(site_settings, context={"request": request}).data, status=status.HTTP_200_OK)


class ContactMessageCreateView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ContactMessageSerializer

    @extend_schema(
        tags=["Storefront & Settings"],
        description="Submit a customer inquiry or support message (rate-limited to 1 per minute per IP)",
        request=ContactMessageSerializer,
        responses={201: ContactMessageSerializer},
    )
    def create(self, request, *args, **kwargs):
        identity = request.META.get("REMOTE_ADDR", "unknown")
        digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
        rate_key = f"api:rate:contact:{digest}"

        if not cache.add(rate_key, True, timeout=60):
            return Response(
                {"detail": "Please wait one minute before sending another message."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        if settings.ORDER_NOTIFICATION_EMAIL:
            transaction.on_commit(lambda: _notify_contact(message.pk))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

