import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F

from catalog.models import Product, ProductVariant
from .models import Order

logger = logging.getLogger(__name__)


def send_order_notifications(order_id):
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    subject = f"طلب جديد {order.order_number}"
    lines = [
        f"رقم الطلب: {order.order_number}", f"العميل: {order.customer_name}",
        f"الهاتف: {order.phone}", f"الإجمالي: {order.total}", "", "المنتجات:",
    ]
    lines.extend(f"- {item.quantity} × {item.product_name} ({item.sku})" for item in order.items.all())
    recipients = list(dict.fromkeys(email for email in [order.email, settings.ORDER_NOTIFICATION_EMAIL] if email))
    if not recipients:
        return
    try:
        send_mail(subject, "\n".join(lines), settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:
        logger.exception("Could not send notifications for order %s", order.order_number)


@transaction.atomic
def restore_order_stock(order_id):
    if Order.objects.filter(pk=order_id, stock_restored=False).update(stock_restored=True) != 1:
        return False
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    for item in order.items.all():
        if item.variant_id:
            ProductVariant.objects.filter(pk=item.variant_id).update(stock_quantity=F("stock_quantity") + item.quantity)
        elif item.product_id:
            Product.objects.filter(pk=item.product_id).update(stock_quantity=F("stock_quantity") + item.quantity)
    return True
