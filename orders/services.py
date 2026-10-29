import logging
import re

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone

from catalog.models import Product, ProductVariant
from .models import Coupon, Order, OrderNotification

logger = logging.getLogger(__name__)


def clean_phone_for_whatsapp(phone):
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if not digits:
        return ""
    if digits.startswith("0") and len(digits) == 11:
        return "20" + digits[1:]
    if digits.startswith("20") and len(digits) == 12:
        return digits
    if len(digits) == 10:
        return "20" + digits
    return digits


def get_admin_notification_emails():
    raw = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "") or ""
    if isinstance(raw, (list, tuple)):
        emails = [str(e).strip() for e in raw if str(e).strip()]
    else:
        emails = [e.strip() for e in str(raw).replace(";", ",").split(",") if e.strip()]
    if not emails:
        admins = getattr(settings, "ADMINS", ())
        emails = [admin[1].strip() for admin in admins if len(admin) > 1 and admin[1].strip()]
    if not emails:
        err_email = getattr(settings, "ERROR_NOTIFICATION_EMAIL", "").strip()
        if err_email:
            emails = [err_email]
    return list(dict.fromkeys(emails))


def get_site_url():
    url = getattr(settings, "SITE_URL", "").strip().rstrip("/")
    if url:
        return url
    if getattr(settings, "DEBUG", False):
        return "http://127.0.0.1:8000"
    return "https://rocks-ev.com"


def _fallback_admin_text(order, formatted_date, items):
    lines = [
        "==================================================",
        "           إشعار بطلب جديد | NEW ORDER",
        "         ROCKS ELECTRIC - روكس للكهرباء",
        "==================================================",
        f"رقم الطلب / Order Number: {order.order_number}",
        f"التاريخ / Date: {formatted_date}",
        f"العميل / Customer: {order.customer_name}",
        f"الهاتف / Phone: {order.phone}",
        f"المحافظة / Governorate: {order.governorate} - {order.city}",
        f"العنوان / Address: {order.address}",
        "طريقة الدفع: الدفع عند الاستلام (COD)",
        f"المجموع الإجمالي / Total: {order.total} ج.م",
        "",
        "المنتجات المطلوبة:",
    ]
    lines.extend(f"- {item.quantity} × {item.product_name} ({item.sku}) - {item.total} ج.م" for item in items)
    if order.notes:
        lines.extend(["", f"ملاحظات العميل: {order.notes}"])
    return "\n".join(lines)


def send_order_notifications(order_id, force=False):
    notification, _ = OrderNotification.objects.get_or_create(order_id=order_id)
    if notification.status == "sent" and not force:
        return True

    order = Order.objects.prefetch_related("items").get(pk=order_id)
    admin_emails = get_admin_notification_emails()
    customer_email = order.email.strip() if (order.email and order.email.strip()) else None

    if not admin_emails and not customer_email:
        notification.status = "skipped"
        notification.last_error = "No customer or store notification email is configured."
        notification.save(update_fields=("status", "last_error"))
        return False

    now = timezone.now()
    exclude_statuses = () if force else ("sent", "sending")
    claimed = OrderNotification.objects.filter(pk=notification.pk).exclude(
        status__in=exclude_statuses
    ).update(status="sending", attempts=F("attempts") + 1, last_attempt_at=now)
    if not claimed:
        return notification.status == "sent"

    site_url = get_site_url()
    local_dt = timezone.localtime(order.created_at) if order.created_at else timezone.localtime(now)
    formatted_date = local_dt.strftime("%Y-%m-%d %I:%M %p")
    items = list(order.items.all())
    whatsapp_phone = clean_phone_for_whatsapp(order.phone)
    whatsapp_url = f"https://wa.me/{whatsapp_phone}" if whatsapp_phone else ""

    context = {
        "order": order,
        "items": items,
        "site_url": site_url,
        "admin_order_url": f"{site_url}/admin/orders/order/{order.pk}/change/",
        "controlpanel_order_url": f"{site_url}/dashboard/orders/{order.pk}/edit/",
        "track_order_url": f"{site_url}/checkout/success/{order.public_token}/",
        "formatted_date": formatted_date,
        "whatsapp_phone": whatsapp_phone,
        "whatsapp_url": whatsapp_url,
        "currency": "ج.م",
    }

    try:
        # 1. Send Admin Order Notification
        if admin_emails:
            admin_subject = f"[طلب جديد | New Order] #{order.order_number} - {order.customer_name} ({order.total} ج.م)"
            try:
                admin_html = render_to_string("emails/order_notification_admin.html", context)
                admin_text = render_to_string("emails/order_notification_admin.txt", context)
            except Exception as tmpl_err:
                logger.warning("Could not render admin email templates (%s); using fallback text", tmpl_err)
                admin_html = None
                admin_text = _fallback_admin_text(order, formatted_date, items)

            send_mail(
                subject=admin_subject,
                message=admin_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                html_message=admin_html,
                fail_silently=False,
            )

        # 2. Send Customer Order Confirmation (if customer email is provided)
        if customer_email:
            try:
                customer_subject = f"تم استلام طلبك بنجاح #{order.order_number} | ROCKS ELECTRIC"
                customer_html = render_to_string("emails/customer_order_confirmation.html", context)
                customer_text = render_to_string("emails/customer_order_confirmation.txt", context)
                send_mail(
                    subject=customer_subject,
                    message=customer_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[customer_email],
                    html_message=customer_html,
                    fail_silently=False,
                )
            except Exception as cust_exc:
                logger.warning("Could not send confirmation to customer %s: %s", customer_email, cust_exc)

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
