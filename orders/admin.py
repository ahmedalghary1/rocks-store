from django.contrib import admin
from .models import Coupon, Order, OrderItem
from .services import restore_order_stock


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "price", "quantity", "total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "phone", "email", "total", "status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "customer_name", "phone", "email")
    inlines = (OrderItemInline,)

    def save_model(self, request, obj, form, change):
        previous_status = Order.objects.filter(pk=obj.pk).values_list("status", flat=True).first() if change else None
        super().save_model(request, obj, form, change)
        if obj.status == "cancelled" and previous_status != "cancelled":
            restore_order_stock(obj.pk)


admin.site.register(Coupon)
