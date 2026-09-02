from django.contrib import admin
from .models import Coupon, Order, OrderItem, OrderNotification, ShippingZone
from .services import restore_order_stock, send_order_notifications


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sku", "price", "quantity", "total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "phone", "total", "status", "notification_status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "customer_name", "phone", "email")
    inlines = (OrderItemInline,)

    @admin.display(description="الإشعار")
    def notification_status(self, obj):
        try:
            return obj.notification.get_status_display()
        except OrderNotification.DoesNotExist:
            return "لم يُنشأ"

    def save_model(self, request, obj, form, change):
        previous_status = Order.objects.filter(pk=obj.pk).values_list("status", flat=True).first() if change else None
        super().save_model(request, obj, form, change)
        if obj.status == "cancelled" and previous_status != "cancelled":
            restore_order_stock(obj.pk)


admin.site.register(Coupon)
admin.site.register(ShippingZone)


@admin.register(OrderNotification)
class OrderNotificationAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "attempts", "last_attempt_at", "sent_at")
    list_filter = ("status",)
    search_fields = ("order__order_number", "last_error")
    readonly_fields = ("order", "status", "attempts", "last_error", "last_attempt_at", "sent_at")
    actions = ("retry_selected",)

    @admin.action(description="إعادة محاولة إرسال الإشعارات المحددة")
    def retry_selected(self, request, queryset):
        sent = sum(1 for item in queryset if send_order_notifications(item.order_id))
        self.message_user(request, f"تم إرسال {sent} من {queryset.count()} إشعار.")
