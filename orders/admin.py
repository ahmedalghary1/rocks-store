from django.contrib import admin
from .models import Coupon, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "price", "quantity", "total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "phone", "total", "status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "customer_name", "phone")
    inlines = (OrderItemInline,)


admin.site.register(Coupon)
