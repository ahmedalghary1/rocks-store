from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.views.generic import TemplateView
from config.admin_site import rocks_admin_site
from core import views as core_views

urlpatterns = [
    path("dashboard/", include("controlpanel.urls")),
    path("admin/", rocks_admin_site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("cart/", include("cart.urls")),
    path("checkout/", include("orders.urls")),
    path("account/", include("accounts.urls")),
    path("auth/", include("django.contrib.auth.urls")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", core_views.sitemap, name="sitemap"),
]
urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    path("products/", include("catalog.urls")),
    prefix_default_language=False,
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
