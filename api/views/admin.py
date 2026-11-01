from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from core.models import ContactMessage
from orders.models import Order
from orders.services import restore_order_stock
from api.serializers.admin import (
    AdminContactMessageStatusSerializer,
    AdminDashboardMetricsSerializer,
    AdminOrderUpdateStatusSerializer,
)
from api.serializers.core import ContactMessageSerializer
from api.serializers.orders import OrderSerializer

User = get_user_model()


class AdminDashboardMetricsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    @extend_schema(
        tags=["Admin Management"],
        description="Get dashboard KPIs: orders, revenue, inventory alerts, and unread customer messages",
        responses=AdminDashboardMetricsSerializer,
    )
    def get(self, request):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        orders_qs = Order.objects.all()
        total_orders = orders_qs.count()
        pending_orders = orders_qs.filter(status="pending").count()
        confirmed_orders = orders_qs.filter(status="confirmed").count()
        processing_orders = orders_qs.filter(status="processing").count()
        shipped_orders = orders_qs.filter(status="shipped").count()
        delivered_orders = orders_qs.filter(status="delivered").count()
        cancelled_orders = orders_qs.filter(status="cancelled").count()

        valid_revenue_orders = orders_qs.exclude(status="cancelled")
        total_rev = valid_revenue_orders.aggregate(s=Sum("total"))["s"] or Decimal("0.00")
        month_rev = valid_revenue_orders.filter(created_at__gte=start_of_month).aggregate(s=Sum("total"))["s"] or Decimal("0.00")

        products_qs = Product.objects.all()
        total_products = products_qs.count()
        out_of_stock_products = products_qs.filter(stock_quantity=0).count()
        low_stock_products = products_qs.filter(stock_quantity__gt=0, stock_quantity__lte=5).count()

        total_customers = User.objects.filter(is_staff=False).count()
        unread_messages = ContactMessage.objects.filter(is_read=False).count()

        data = {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "processing_orders": processing_orders,
            "shipped_orders": shipped_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": total_rev,
            "month_revenue": month_rev,
            "total_products": total_products,
            "out_of_stock_products": out_of_stock_products,
            "low_stock_products": low_stock_products,
            "total_customers": total_customers,
            "unread_messages": unread_messages,
        }
        return Response(AdminDashboardMetricsSerializer(data).data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Admin Management"],
        description="List all customer orders with filtering by status and search",
        parameters=[
            OpenApiParameter(name="status", description="Filter by status (pending, confirmed, processing, shipped, delivered, cancelled)", required=False, type=str),
            OpenApiParameter(name="payment_status", description="Filter by payment status (unpaid, pending, paid, refunded)", required=False, type=str),
            OpenApiParameter(name="search", description="Search by order number, customer name, phone, or email", required=False, type=str),
        ],
    ),
    retrieve=extend_schema(tags=["Admin Management"], description="Retrieve detailed order breakdown by ID"),
)
class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = OrderSerializer
    search_fields = ("order_number", "customer_name", "phone", "email")

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items").all().order_by("-created_at")
        status_param = self.request.GET.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        payment_status_param = self.request.GET.get("payment_status")
        if payment_status_param:
            qs = qs.filter(payment_status=payment_status_param)
        return qs

    @extend_schema(
        tags=["Admin Management"],
        description="Update order fulfillment status or payment status. When transitioning to 'cancelled', stock is automatically restored.",
        request=AdminOrderUpdateStatusSerializer,
        responses=OrderSerializer,
    )
    @action(detail=True, methods=["patch"], url_path="update-status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = AdminOrderUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")
        new_payment_status = serializer.validated_data.get("payment_status")
        previous_status = order.status

        update_fields = []
        if new_status:
            if previous_status == "cancelled" and new_status != "cancelled":
                return Response(
                    {"detail": "A cancelled order cannot be reopened once inventory has been restored."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order.status = new_status
            update_fields.append("status")

        if new_payment_status:
            order.payment_status = new_payment_status
            update_fields.append("payment_status")

        if update_fields:
            update_fields.append("updated_at")
            order.save(update_fields=update_fields)

        if new_status == "cancelled" and previous_status != "cancelled":
            restore_order_stock(order.pk)
            order.refresh_from_db()

        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Admin Management"],
        description="List customer contact submissions with read/unread filter",
        parameters=[OpenApiParameter(name="is_read", description="Filter by read status (true/false)", required=False, type=bool)],
    ),
    retrieve=extend_schema(tags=["Admin Management"], description="Retrieve contact message details"),
)
class AdminContactMessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ContactMessageSerializer

    def get_queryset(self):
        qs = ContactMessage.objects.all().order_by("-created_at")
        is_read_param = self.request.GET.get("is_read")
        if is_read_param is not None:
            if is_read_param.lower() in ("true", "1"):
                qs = qs.filter(is_read=True)
            elif is_read_param.lower() in ("false", "0"):
                qs = qs.filter(is_read=False)
        return qs

    @extend_schema(
        tags=["Admin Management"],
        description="Mark customer message as read or unread",
        request=AdminContactMessageStatusSerializer,
        responses=ContactMessageSerializer,
    )
    @action(detail=True, methods=["patch"], url_path="set-read")
    def set_read(self, request, pk=None):
        message = self.get_object()
        serializer = AdminContactMessageStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message.is_read = serializer.validated_data["is_read"]
        message.save(update_fields=["is_read"])
        return Response(ContactMessageSerializer(message).data, status=status.HTTP_200_OK)

