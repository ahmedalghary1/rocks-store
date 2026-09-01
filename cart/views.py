from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from catalog.models import Product, ProductVariant
from .service import Cart


def detail(request):
    cart = Cart(request)
    return render(request, "cart/cart.html", {"cart": cart, "cart_items": cart.items()})


@require_POST
def add(request, product_id):
    cart = Cart(request)
    try:
        cart.add(product_id, request.POST.get("quantity", 1), request.POST.get("variant_id") or None)
    except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist) as exc:
        message = str(exc) or "تعذرت إضافة المنتج."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect("cart:detail")
    message = "تمت إضافة المنتج إلى السلة"
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": message, "count": cart.count, "total": str(cart.total)})
    messages.success(request, message)
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("cart:detail")


@require_POST
def update(request, item_key):
    cart = Cart(request)
    try:
        cart.update(item_key, request.POST.get("quantity", 1))
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            updated_item = next((item for item in cart.items() if item["key"] == str(item_key)), None)
            return JsonResponse({
                "ok": True,
                "message": "تم تحديث الكمية",
                "quantity": updated_item["quantity"] if updated_item else 0,
                "item_total": str(updated_item["total"]) if updated_item else "0.00",
                "count": cart.count,
                "subtotal": str(cart.subtotal),
                "shipping": str(cart.shipping),
                "discount": str(cart.discount),
                "total": str(cart.total),
            })
        messages.success(request, "تم تحديث الكمية")
    except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist) as exc:
        message = str(exc) or "تعذر تحديث الكمية."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
    return redirect("cart:detail")


@require_POST
def remove(request, item_key):
    Cart(request).remove(item_key)
    messages.info(request, "تم حذف المنتج من السلة")
    return redirect("cart:detail")


@require_POST
def apply_coupon(request):
    if Cart(request).apply_coupon(request.POST.get("code", "")):
        messages.success(request, "تم تطبيق كوبون الخصم")
    else:
        messages.error(request, "الكوبون غير صالح أو لا ينطبق على هذه السلة")
    return redirect("cart:detail")


@require_POST
def remove_coupon(request):
    Cart(request).remove_coupon()
    messages.info(request, "تمت إزالة الكوبون")
    return redirect("cart:detail")
