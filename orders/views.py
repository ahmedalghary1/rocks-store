from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from secrets import token_hex
from cart.service import Cart
from catalog.models import Product
from .forms import CheckoutForm
from .models import OrderItem


@transaction.atomic
def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.warning(request, "السلة فارغة. أضف منتجًا قبل إتمام الطلب.")
        return redirect("catalog:list")
    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=[item["product"].id for item in items], is_active=True)}
        if len(locked) != len(items) or any(locked[item["product"].id].stock_quantity < item["quantity"] for item in items):
            messages.error(request, "تغيّرت الكمية المتاحة لأحد المنتجات. راجع السلة وحاول مجددًا.")
            return redirect("cart:detail")
        order = form.save(commit=False)
        order.order_number = f"RK-{timezone.now():%y%m%d%H%M%S}-{token_hex(2).upper()}"
        order.user = request.user if request.user.is_authenticated else None
        order.subtotal, order.shipping_cost, order.discount, order.total = cart.subtotal, cart.shipping, cart.discount, cart.total
        order.save()
        for item in items:
            product = locked[item["product"].id]
            OrderItem.objects.create(order=order, product=product, product_name=product.name, sku=product.sku, price=product.price, quantity=item["quantity"], total=item["total"])
            product.stock_quantity -= item["quantity"]
            product.save(update_fields=("stock_quantity",))
        if cart.coupon:
            cart.coupon.usage_count += 1
            cart.coupon.save(update_fields=("usage_count",))
        request.session["last_order"] = order.order_number
        cart.clear()
        return redirect("orders:success", order_number=order.order_number)
    return render(request, "orders/checkout.html", {"form": form, "cart": cart, "cart_items": items})


def success(request, order_number):
    from django.shortcuts import get_object_or_404
    from .models import Order
    if request.session.get("last_order") != order_number and not request.user.is_staff:
        return redirect("core:home")
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_number=order_number)
    return render(request, "orders/success.html", {"order": order})
