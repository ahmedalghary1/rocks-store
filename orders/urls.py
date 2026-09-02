from django.urls import path
from . import views
app_name = "orders"
urlpatterns = [
    path("", views.checkout, name="checkout"),
    path("track/", views.track, name="track"),
    path("success/<uuid:public_token>/", views.success, name="success"),
]
