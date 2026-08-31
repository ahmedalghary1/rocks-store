from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("search/suggestions/", views.suggestions, name="suggestions"),
    path("<slug:slug>/quick-view/", views.quick_view, name="quick_view"),
    path("<slug:slug>/", views.product_detail, name="detail"),
]
