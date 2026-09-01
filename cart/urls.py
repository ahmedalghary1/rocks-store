from django.urls import path
from . import views

app_name = "cart"
urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/<int:product_id>/", views.add, name="add"),
    path("update/<str:item_key>/", views.update, name="update"),
    path("remove/<str:item_key>/", views.remove, name="remove"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),
]
