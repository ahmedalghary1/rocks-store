from django.contrib import admin
from .models import Banner, Subscriber


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "is_active", "sort_order")
    list_filter = ("location", "is_active")
    search_fields = ("title", "subtitle")


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("email",)
