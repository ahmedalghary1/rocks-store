from django.urls import path
from . import views
app_name = "orders"
urlpatterns = [path("", views.checkout, name="checkout"), path("success/<str:order_number>/", views.success, name="success")]
