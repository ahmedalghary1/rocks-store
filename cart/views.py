from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .service import Cart


def detail(request):
    cart = Cart(request)
    return render(request, "cart/cart.html", {"cart": cart, "cart_items": cart.items()})


@require_POST
def add(request, product_id):
    cart = Cart(request)
    cart.add(product_id, request.POST.get("quantity", 1))
    message = "تمت إضافة المنتج إلى السلة"
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": message, "count": sum(cart.data.values()), "total": str(cart.total)})
    messages.success(request, message)
    return redirect(request.POST.get("next", "cart:detail"))


@require_POST
def update(request, product_id):
    cart = Cart(request)
    cart.update(product_id, request.POST.get("quantity", 1))
    messages.success(request, "تم تحديث الكمية")
    return redirect("cart:detail")


@require_POST
def remove(request, product_id):
    Cart(request).remove(product_id)
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
