from .models import SiteSettings
from catalog.models import Category
from django.templatetags.static import static


def site_context(request):
    settings_obj = SiteSettings.objects.first()
    canonical_path = request.path
    page_number = request.GET.get("page", "")
    if page_number.isdigit() and int(page_number) > 1 and set(request.GET) == {"page"}:
        canonical_path = f"{canonical_path}?page={page_number}"
    canonical_url = request.build_absolute_uri(canonical_path)
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
        "default_og_image": request.build_absolute_uri(static("images/rocks-logo-social-black.webp")),
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }
