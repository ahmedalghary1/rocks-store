import uuid
from decimal import Decimal

import hashlib

from django.contrib import messages
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from cart.service import Cart
from catalog.models import Product, ProductVariant
from .forms import CheckoutForm, TrackOrderForm
from .models import Coupon, Order, OrderItem, OrderNotification, ShippingZone


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
        messages.warning(request, "Your cart is empty. Add a product before checkout.")
        return redirect("catalog:list")
    session_token = _checkout_token(request)
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        posted_token = request.POST.get("checkout_token", "")
        if posted_token != session_token:
            form.add_error(None, "Your checkout session has expired. Refresh the page and try again.")
        else:
            try:
                token = uuid.UUID(posted_token)
            except (ValueError, TypeError):
                form.add_error(None, "The checkout token is invalid.")
            else:
                existing = Order.objects.filter(checkout_token=token).first()
                if existing:
                    request.session["last_order_token"] = str(existing.public_token)
                    return redirect("orders:success", public_token=existing.public_token)
                try:
                    with transaction.atomic():
                        subtotal = sum((item["total"] for item in items), Decimal("0"))
                        zone = ShippingZone.objects.get(name=form.cleaned_data["governorate"], is_active=True)
                        shipping = zone.cost_for(subtotal)
                        discount = Decimal("0")
                        claimed_coupon = None
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
                                    claimed_coupon = coupon
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
                        order.payment_method = "cod"
                        order.payment_status = "unpaid"
                        order.coupon = claimed_coupon
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
                        OrderNotification.objects.create(order=order)
                except InsufficientStock:
                    messages.error(request, "Available stock has changed. Review your cart and try again.")
                    return redirect("cart:detail")
                except IntegrityError:
                    existing = Order.objects.filter(checkout_token=token).first()
                    if not existing:
                        raise
                    order = existing
                request.session["last_order_token"] = str(order.public_token)
                request.session.pop("checkout_token", None)
                cart.clear()
                return redirect("orders:success", public_token=order.public_token)
    shipping = cart.shipping
    selected_governorate = request.POST.get("governorate", "")
    if selected_governorate:
        zone = ShippingZone.objects.filter(name=selected_governorate, is_active=True).first()
        if zone:
            shipping = zone.cost_for(cart.subtotal)
    return render(request, "orders/checkout.html", {
        "form": form, "cart": cart, "cart_items": items, "checkout_token": session_token,
        "shipping_cost": shipping,
        "checkout_total": max(Decimal("0"), cart.subtotal + shipping - cart.discount),
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


def track(request):
    form = TrackOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identity = request.META.get("REMOTE_ADDR", "unknown")
        digest = hashlib.sha256(f"track:{identity}".encode()).hexdigest()[:24]
        if not cache.add(f"order-track:{digest}", True, timeout=3):
            form.add_error(None, "Please wait a moment before trying again.")
        else:
            order = Order.objects.filter(
                order_number__iexact=form.cleaned_data["order_number"].strip(),
                phone=form.cleaned_data["phone"],
            ).first()
            if order:
                request.session["last_order_token"] = str(order.public_token)
                return redirect("orders:success", public_token=order.public_token)
            form.add_error(None, "No order was found with these details.")
    return render(request, "orders/track.html", {"form": form})
