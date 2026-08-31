from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from catalog.models import Category, Product
from .models import ContactMessage


def home(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    context = {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True)[:6],
        "featured_products": products.filter(is_featured=True)[:8],
        "best_sellers": products.filter(is_best_seller=True)[:4],
        "new_products": products.filter(is_new=True)[:8],
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        ContactMessage.objects.create(
            name=request.POST.get("name", "").strip(), phone=request.POST.get("phone", "").strip(),
            email=request.POST.get("email", "").strip(), subject=request.POST.get("subject", "استفسار").strip(),
            message=request.POST.get("message", "").strip(),
        )
        messages.success(request, "وصلت رسالتك، وسيتواصل معك فريق ROCKS قريبًا.")
        return redirect("core:contact")
    return render(request, "core/contact.html")


def wishlist(request):
    ids = request.session.get("wishlist", [])
    products = Product.objects.filter(id__in=ids, is_active=True).select_related("category")
    return render(request, "core/wishlist.html", {"products": products})


@require_POST
def wishlist_toggle(request, product_id):
    wishlist = request.session.get("wishlist", [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        active = False
    else:
        wishlist.append(product_id)
        active = True
    request.session["wishlist"] = wishlist
    return JsonResponse({"ok": True, "active": active, "count": len(wishlist)})


def sitemap(request):
    base = request.build_absolute_uri("/").rstrip("/")
    urls = ["/", "/products/", "/about/", "/contact/"] + [p.get_absolute_url() for p in Product.objects.filter(is_active=True)]
    body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{base}{url}</loc></url>" for url in urls) + "</urlset>"
    return HttpResponse(body, content_type="application/xml")


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
