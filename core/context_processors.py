from .models import SiteSettings
from catalog.models import Category
from django.templatetags.static import static
from django.urls import translate_url
from .seo import absolute_url, language_urls, json_ld, store_schema


def site_context(request):
    settings_obj = SiteSettings.objects.first()
    canonical_path = request.path
    page_number = request.GET.get("page", "")
    if page_number.isdigit() and int(page_number) > 1 and set(request.GET) == {"page"}:
        canonical_path = f"{canonical_path}?page={page_number}"
    canonical_url = absolute_url(request, canonical_path)
    default_image = absolute_url(request, static("images/rocks-logo-social-black.webp"))
    cart_data = request.session.get("cart", {})
    cart_count = 0
    if isinstance(cart_data, dict):
        for value in cart_data.values():
            try:
                cart_count += max(0, int(value))
            except (TypeError, ValueError):
                continue
    return {
        "site_settings": settings_obj,
        "navigation_categories": Category.objects.filter(is_active=True),
        "cart_count": cart_count,
        "canonical_url": canonical_url,
        "default_og_image": default_image,
        "language_alternates": language_urls(request, canonical_path),
        "language_switch_paths": {code: translate_url(request.get_full_path(), code) for code in ("en", "ar")},
        "store_json_ld": json_ld(store_schema(request, settings_obj, default_image)),
        "sitemap_url": absolute_url(request, "/sitemap.xml"),
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }
