import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Product, ProductVariant
from .models import Coupon, Order, OrderNotification

logger = logging.getLogger(__name__)


def send_order_notifications(order_id):
    notification, _ = OrderNotification.objects.get_or_create(order_id=order_id)
    if notification.status == "sent":
        return True
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    subject = f"طلب جديد {order.order_number}"
    lines = [
        f"رقم الطلب: {order.order_number}", f"العميل: {order.customer_name}",
        f"الهاتف: {order.phone}", f"الإجمالي: {order.total}", "", "المنتجات:",
    ]
    lines.extend(f"- {item.quantity} × {item.product_name} ({item.sku})" for item in order.items.all())
    recipients = list(dict.fromkeys(email for email in [order.email, settings.ORDER_NOTIFICATION_EMAIL] if email))
    if not recipients:
        notification.status = "skipped"
        notification.last_error = "No customer or store notification email is configured."
        notification.save(update_fields=("status", "last_error"))
        return False
    now = timezone.now()
    claimed = OrderNotification.objects.filter(pk=notification.pk).exclude(
        status__in=("sent", "sending")
    ).update(status="sending", attempts=F("attempts") + 1, last_attempt_at=now)
    if not claimed:
        return notification.status == "sent"
    try:
        send_mail(subject, "\n".join(lines), settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception as exc:
        notification.status = "failed"
        notification.last_error = str(exc)[:2000]
        notification.save(update_fields=("status", "last_error"))
        logger.exception("Could not send notifications for order %s", order.order_number)
        return False
    notification.status = "sent"
    notification.last_error = ""
    notification.sent_at = timezone.now()
    notification.save(update_fields=("status", "last_error", "sent_at"))
    return True


@transaction.atomic
def restore_order_stock(order_id):
    if Order.objects.filter(pk=order_id, stock_restored=False).update(stock_restored=True) != 1:
        return False
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    for item in order.items.all():
        if item.variant_id:
            ProductVariant.objects.filter(pk=item.variant_id).update(stock_quantity=F("stock_quantity") + item.quantity)
        elif item.product_id and item.sku == item.product.sku:
            Product.objects.filter(pk=item.product_id).update(stock_quantity=F("stock_quantity") + item.quantity)
        else:
            logger.error("Could not restore inventory target for order item %s (%s)", item.pk, item.sku)
    if order.coupon_id:
        Coupon.objects.filter(pk=order.coupon_id, usage_count__gt=0).update(usage_count=F("usage_count") - 1)
    return True
