from .models import SiteSettings


def site_context(request):
    settings_obj = SiteSettings.objects.first()
    return {"site_settings": settings_obj, "cart_count": sum(request.session.get("cart", {}).values())}
