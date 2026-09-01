import uuid
from decimal import Decimal

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cart.service import Cart
from catalog.models import Product, ProductVariant
from .forms import CheckoutForm
from .models import Coupon, Order, OrderItem
from .services import send_order_notifications


class InsufficientStock(Exception):
    pass


def _checkout_token(request):
    token = request.session.get("checkout_token")
    if not token:
        token = str(uuid.uuid4())
        request.session["checkout_token"] = token
    return token


def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.warning(request, "السلة فارغة. أضف منتجًا قبل إتمام الطلب.")
        return redirect("catalog:list")
    session_token = _checkout_token(request)
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        posted_token = request.POST.get("checkout_token", "")
        if posted_token != session_token:
            form.add_error(None, "انتهت جلسة تأكيد الطلب. حدّث الصفحة وحاول مرة أخرى.")
        else:
            try:
                token = uuid.UUID(posted_token)
            except (ValueError, TypeError):
                form.add_error(None, "رمز تأكيد الطلب غير صالح.")
            else:
                existing = Order.objects.filter(checkout_token=token).first()
                if existing:
                    request.session["last_order_token"] = str(existing.public_token)
                    return redirect("orders:success", public_token=existing.public_token)
                try:
                    created_order = True
                    with transaction.atomic():
                        subtotal = sum((item["total"] for item in items), Decimal("0"))
                        shipping = cart.shipping
                        discount = Decimal("0")
                        coupon = cart.coupon
                        if coupon:
                            proposed = coupon.discount_for(subtotal)
                            if proposed > 0:
                                now = timezone.now()
                                claimed = Coupon.objects.filter(
                                    pk=coupon.pk, is_active=True, start_date__lte=now, end_date__gte=now,
                                    usage_count__lt=F("usage_limit"), minimum_order__lte=subtotal,
                                ).update(usage_count=F("usage_count") + 1)
                                if claimed:
                                    discount = proposed
                        for item in items:
                            stock_model = ProductVariant if item["variant"] else Product
                            filters = {
                                "pk": item["variant"].pk if item["variant"] else item["product"].pk,
                                "is_active": True, "stock_quantity__gte": item["quantity"],
                            }
                            updated = stock_model.objects.filter(**filters).update(
                                stock_quantity=F("stock_quantity") - item["quantity"]
                            )
                            if updated != 1:
                                raise InsufficientStock
                        order = form.save(commit=False)
                        order.payment_status = "pending" if order.payment_method == "bank" else "unpaid"
                        order.checkout_token = token
                        order.order_number = f"RK-{timezone.now():%y%m%d}-{uuid.uuid4().hex[:12].upper()}"
                        order.user = request.user if request.user.is_authenticated else None
                        order.subtotal, order.shipping_cost, order.discount = subtotal, shipping, discount
                        order.total = max(Decimal("0"), subtotal + shipping - discount)
                        order.save()
                        OrderItem.objects.bulk_create([
                            OrderItem(
                                order=order, product=item["product"], variant=item["variant"],
                                product_name=item["product"].name, sku=item["sku"], price=item["price"],
                                quantity=item["quantity"], total=item["total"],
                            ) for item in items
                        ])
                except InsufficientStock:
                    messages.error(request, "تغيّرت الكمية المتاحة لأحد المنتجات. راجع السلة وحاول مجددًا.")
                    return redirect("cart:detail")
                except IntegrityError:
                    existing = Order.objects.filter(checkout_token=token).first()
                    if not existing:
                        raise
                    order = existing
                    created_order = False
                request.session["last_order_token"] = str(order.public_token)
                request.session.pop("checkout_token", None)
                cart.clear()
                if created_order:
                    transaction.on_commit(lambda: send_order_notifications(order.pk))
                return redirect("orders:success", public_token=order.public_token)
    return render(request, "orders/checkout.html", {
        "form": form, "cart": cart, "cart_items": items, "checkout_token": session_token,
    })


def success(request, public_token):
    order = get_object_or_404(Order.objects.prefetch_related("items"), public_token=public_token)
    allowed = (
        request.user.is_staff
        or (request.user.is_authenticated and order.user_id == request.user.id)
        or request.session.get("last_order_token") == str(public_token)
    )
    if not allowed:
        return redirect("core:home")
    return render(request, "orders/success.html", {"order": order})
