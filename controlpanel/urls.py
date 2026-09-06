from django.urls import path

from . import views

app_name = "controlpanel"

urlpatterns = [
    path("login/", views.PanelLoginView.as_view(), name="login"),
    path("", views.index, name="index"),
    path("<slug:resource>/", views.resource_list, name="list"),
    path("<slug:resource>/new/", views.resource_form, name="create"),
    path("<slug:resource>/<int:pk>/edit/", views.resource_form, name="edit"),
    path("<slug:resource>/<int:pk>/delete/", views.resource_delete, name="delete"),
]
