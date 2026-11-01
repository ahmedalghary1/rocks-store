from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from api import views

app_name = "api"

router = DefaultRouter()
router.register(r"auth/addresses", views.AddressViewSet, basename="address")
router.register(r"auth/favorites", views.FavoriteViewSet, basename="favorite")
router.register(r"catalog/categories", views.CategoryViewSet, basename="category")
router.register(r"catalog/products", views.ProductViewSet, basename="product")
router.register(r"orders/my-orders", views.UserOrdersViewSet, basename="user-order")
router.register(r"admin/orders", views.AdminOrderViewSet, basename="admin-order")
router.register(r"admin/contact-messages", views.AdminContactMessageViewSet, basename="admin-contact-message")

urlpatterns = [
    # JWT Authentication
    path("auth/register/", views.RegisterView.as_view(), name="auth-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("auth/me/", views.UserProfileView.as_view(), name="auth-me"),
    path("auth/change-password/", views.ChangePasswordView.as_view(), name="auth-change-password"),

    # Catalog
    path("catalog/homepage/", views.HomepageView.as_view(), name="catalog-homepage"),

    # Shopping Cart
    path("cart/", views.CartView.as_view(), name="cart-detail"),
    path("cart/items/", views.CartItemsView.as_view(), name="cart-items"),
    path("cart/items/<str:item_key>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/coupon/", views.CartCouponView.as_view(), name="cart-coupon"),
    path("cart/clear/", views.CartClearView.as_view(), name="cart-clear"),

    # Shipping, Coupons & Checkout
    path("orders/shipping-zones/", views.ShippingZoneListView.as_view(), name="shipping-zones"),
    path("orders/validate-coupon/", views.ValidateCouponView.as_view(), name="validate-coupon"),
    path("orders/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/track/", views.OrderTrackView.as_view(), name="order-track"),
    path("orders/receipt/<uuid:public_token>/", views.PublicOrderReceiptView.as_view(), name="order-receipt"),

    # Marketing
    path("marketing/banners/", views.BannerListView.as_view(), name="marketing-banners"),
    path("marketing/newsletter/", views.NewsletterSubscribeView.as_view(), name="newsletter-subscribe"),

    # Storefront Core
    path("core/settings/", views.SiteSettingsView.as_view(), name="site-settings"),
    path("core/contact/", views.ContactMessageCreateView.as_view(), name="contact-message"),

    # Admin Management
    path("admin/metrics/", views.AdminDashboardMetricsView.as_view(), name="admin-metrics"),

    # Router URLs (Categories, Products, Addresses, User Orders, Admin Orders/Messages)
    path("", include(router.urls)),
]

