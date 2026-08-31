from django.contrib import admin
from .models import ContactMessage, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "phone", "email", "currency")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "phone", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "phone", "email", "subject")
