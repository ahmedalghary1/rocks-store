from rest_framework import serializers
from orders.models import Order


class AdminDashboardMetricsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    confirmed_orders = serializers.IntegerField()
    processing_orders = serializers.IntegerField()
    shipped_orders = serializers.IntegerField()
    delivered_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    month_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    unread_messages = serializers.IntegerField()


class AdminOrderUpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUSES, required=False)
    payment_status = serializers.ChoiceField(choices=Order.PAYMENT_STATUSES, required=False)


class AdminContactMessageStatusSerializer(serializers.Serializer):
    is_read = serializers.BooleanField(required=True)

