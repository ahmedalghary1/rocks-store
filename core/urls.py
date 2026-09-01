from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"), path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"), path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<int:product_id>/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("privacy/", views.legal_page, {"template_name": "core/privacy.html"}, name="privacy"),
    path("terms/", views.legal_page, {"template_name": "core/terms.html"}, name="terms"),
    path("shipping-policy/", views.legal_page, {"template_name": "core/shipping_policy.html"}, name="shipping_policy"),
    path("returns-policy/", views.legal_page, {"template_name": "core/returns_policy.html"}, name="returns_policy"),
    path("health/", views.health, name="health"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
