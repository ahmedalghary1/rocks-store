from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"), path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"), path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<int:product_id>/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
