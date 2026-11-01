from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from marketing.models import Banner, Subscriber
from api.serializers.marketing import BannerSerializer, NewsletterSubscriberSerializer


class BannerListView(generics.ListAPIView):
    serializer_class = BannerSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None

    @extend_schema(
        tags=["Marketing"],
        description="List active banners, optionally filtered by location (hero, offer, promo)",
        parameters=[OpenApiParameter(name="location", description="Banner location (hero, offer, promo)", required=False, type=str)],
    )
    def get_queryset(self):
        now = timezone.now()
        qs = Banner.objects.filter(is_active=True).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=now),
            Q(end_date__isnull=True) | Q(end_date__gte=now),
        )
        location = self.request.GET.get("location")
        if location:
            qs = qs.filter(location=location)
        return qs.order_by("sort_order", "pk")


class NewsletterSubscribeView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Marketing"],
        description="Subscribe email to newsletter",
        request=NewsletterSubscriberSerializer,
        responses={200: OpenApiResponse(description="Subscribed successfully")},
    )
    def post(self, request):
        serializer = NewsletterSubscriberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Thank you for subscribing to our newsletter!"}, status=status.HTTP_200_OK)

