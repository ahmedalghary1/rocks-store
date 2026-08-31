from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    category_slug = request.GET.get("category")
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest")
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(short_description__icontains=query) | Q(sku__icontains=query))
    if request.GET.get("available") == "1":
        products = products.filter(stock_quantity__gt=0)
    sort_map = {"newest": "-created_at", "price-low": "price", "price-high": "-price", "name": "name"}
    products = products.order_by(sort_map.get(sort, "-created_at"))
    page_obj = Paginator(products, 24).get_page(request.GET.get("page"))
    return render(request, "catalog/product_list.html", {
        "page_obj": page_obj, "categories": Category.objects.filter(is_active=True), "selected_category": category_slug,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category").prefetch_related("images", "specifications", "variants"), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    return render(request, "catalog/product_detail.html", {"product": product, "related_products": related})


def quick_view(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_active=True)
    return render(request, "catalog/quick_view.html", {"product": product})


def suggestions(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})
    products = Product.objects.filter(is_active=True, name__icontains=query).select_related("category")[:6]
    return JsonResponse({"results": [{"name": p.name, "price": str(p.price), "category": p.category.name, "url": p.get_absolute_url()} for p in products]})
