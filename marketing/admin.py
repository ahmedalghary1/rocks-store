from django.contrib import admin
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "is_active", "sort_order")
    list_filter = ("location", "is_active")
    search_fields = ("title", "subtitle")
