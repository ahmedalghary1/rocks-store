from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import Sum
from django.utils import timezone

from accounts.models import Address
from catalog.admin import CategoryAdmin, ProductAdmin, ProductImageInline, ProductSpecificationInline, ProductVariantInline
from catalog.models import Category, Product, ProductAttribute, ProductImage, ProductSpecification, ProductVariant
from core.admin import ContactMessageAdmin, SiteSettingsAdmin
from core.models import ContactMessage, SiteSettings
from marketing.admin import BannerAdmin, SubscriberAdmin
from marketing.models import Banner, Subscriber
from orders.admin import OrderAdmin, OrderItemInline, OrderNotificationAdmin
from orders.models import Coupon, Order, OrderItem, OrderNotification, ShippingZone
from orders.services import send_order_notifications


APP_LABELS = {
    "auth": "المستخدمون والصلاحيات",
    "catalog": "المنتجات والمخزون",
    "orders": "الطلبات والشحن",
    "core": "إعدادات الموقع والتواصل",
    "marketing": "التسويق والمحتوى",
    "accounts": "عناوين العملاء",
}

MODEL_LABELS = {
    "user": "المستخدمون", "group": "مجموعات الصلاحيات", "address": "عناوين العملاء",
    "category": "التصنيفات", "product": "المنتجات", "productattribute": "خصائص المنتجات",
    "productimage": "صور معرض المنتجات", "productspecification": "مواصفات المنتجات", "productvariant": "متغيرات المنتجات",
    "order": "الطلبات", "orderitem": "عناصر الطلبات", "coupon": "كوبونات الخصم",
    "shippingzone": "مناطق وتكاليف الشحن", "ordernotification": "إشعارات الطلبات",
    "sitesettings": "إعدادات الموقع", "contactmessage": "رسائل التواصل",
    "banner": "البانرات الإعلانية", "subscriber": "مشتركو النشرة البريدية",
}

FIELD_LABELS = {
    "name": "الاسم", "title": "العنوان", "subtitle": "العنوان الفرعي", "slug": "الرابط المختصر",
    "description": "الوصف", "short_description": "الوصف المختصر", "category": "التصنيف",
    "parent": "التصنيف الرئيسي", "image": "الصورة", "main_image": "الصورة الرئيسية",
    "mobile_image": "صورة الهاتف", "alt_text": "النص البديل", "icon": "الأيقونة",
    "sku": "رمز المنتج", "price": "السعر", "old_price": "السعر قبل الخصم",
    "stock_quantity": "الكمية بالمخزون", "is_active": "نشط", "is_featured": "منتج مميز",
    "is_best_seller": "الأكثر مبيعًا", "is_new": "منتج جديد", "sort_order": "ترتيب العرض",
    "meta_title": "عنوان محركات البحث", "meta_description": "وصف محركات البحث",
    "product": "المنتج", "variant": "المتغير", "label": "التسمية", "value": "القيمة",
    "attributes": "الخصائص", "order_number": "رقم الطلب", "customer_name": "اسم العميل",
    "phone": "رقم الهاتف", "second_phone": "هاتف بديل", "email": "البريد الإلكتروني",
    "governorate": "المحافظة", "city": "المدينة", "address": "العنوان", "address_line": "العنوان التفصيلي",
    "notes": "ملاحظات", "subtotal": "إجمالي المنتجات", "shipping_cost": "تكلفة الشحن",
    "discount": "الخصم", "total": "الإجمالي", "status": "الحالة", "payment_method": "طريقة الدفع",
    "payment_status": "حالة الدفع", "created_at": "تاريخ الإنشاء", "updated_at": "آخر تحديث",
    "coupon": "كوبون الخصم", "public_token": "رمز التتبع العام", "checkout_token": "رمز إتمام الطلب",
    "stock_restored": "تمت إعادة المخزون", "product_name": "اسم المنتج وقت الطلب",
    "code": "الكود", "discount_type": "نوع الخصم", "minimum_order": "الحد الأدنى للطلب",
    "start_date": "تاريخ البداية", "end_date": "تاريخ النهاية", "usage_limit": "حد الاستخدام",
    "usage_count": "مرات الاستخدام", "free_shipping_threshold": "حد الشحن المجاني",
    "quantity": "الكمية", "attempts": "عدد المحاولات", "last_error": "آخر خطأ",
    "last_attempt_at": "آخر محاولة", "sent_at": "تاريخ الإرسال", "subject": "الموضوع",
    "message": "الرسالة", "is_read": "تمت القراءة", "company_name": "اسم الشركة",
    "whatsapp": "واتساب", "facebook": "فيسبوك", "instagram": "إنستجرام", "tiktok": "تيك توك",
    "footer_text": "نص الفوتر", "shipping_message": "رسالة الشحن", "currency": "العملة",
    "link": "الرابط", "button_text": "نص الزر", "location": "مكان الظهور",
    "recipient_name": "اسم المستلم", "is_default": "العنوان الافتراضي", "user": "المستخدم",
}

CHOICE_LABELS = {
    "pending": "قيد المراجعة", "confirmed": "تم التأكيد", "processing": "قيد التجهيز",
    "shipped": "تم الشحن", "delivered": "تم التسليم", "cancelled": "ملغي",
    "unpaid": "غير مدفوع", "paid": "مدفوع", "refunded": "مسترد", "sending": "جارٍ الإرسال",
    "sent": "تم الإرسال", "failed": "فشل الإرسال", "skipped": "لا يوجد مستلمون",
    "cod": "الدفع عند الاستلام", "percentage": "نسبة مئوية", "fixed": "قيمة ثابتة",
    "hero": "الهيرو الرئيسي", "offer": "عرض", "promo": "ترويجي",
}


class ArabicAdminMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield and db_field.name in FIELD_LABELS:
            formfield.label = FIELD_LABELS[db_field.name]
        return formfield

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        formfield = super().formfield_for_choice_field(db_field, request, **kwargs)
        if formfield:
            formfield.choices = [(value, CHOICE_LABELS.get(value, label)) for value, label in formfield.choices]
        return formfield


class ArabicChoiceFilter(admin.SimpleListFilter):
    field_name = ""

    def lookups(self, request, model_admin):
        field = model_admin.model._meta.get_field(self.field_name)
        return [(value, CHOICE_LABELS.get(value, label)) for value, label in field.choices]

    def queryset(self, request, queryset):
        return queryset.filter(**{self.field_name: self.value()}) if self.value() else queryset


class OrderStatusFilter(ArabicChoiceFilter):
    title = "حالة الطلب"
    parameter_name = "status"
    field_name = "status"


class PaymentStatusFilter(ArabicChoiceFilter):
    title = "حالة الدفع"
    parameter_name = "payment_status"
    field_name = "payment_status"


class NotificationStatusFilter(ArabicChoiceFilter):
    title = "حالة الإشعار"
    parameter_name = "status"
    field_name = "status"


class BannerLocationFilter(ArabicChoiceFilter):
    title = "مكان الظهور"
    parameter_name = "location"
    field_name = "location"


class DiscountTypeFilter(ArabicChoiceFilter):
    title = "نوع الخصم"
    parameter_name = "discount_type"
    field_name = "discount_type"


class RocksAdminSite(admin.AdminSite):
    site_header = "لوحة تحكم ROCKS"
    site_title = "إدارة ROCKS"
    index_title = "نظرة عامة على المتجر"
    index_template = "admin/index.html"
    enable_nav_sidebar = True

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        order = {name: position for position, name in enumerate(("orders", "catalog", "marketing", "core", "auth", "accounts"))}
        for app in app_list:
            app["name"] = APP_LABELS.get(app["app_label"], app["name"])
            for model in app["models"]:
                model["name"] = MODEL_LABELS.get(model["object_name"].lower(), model["name"])
        return sorted(app_list, key=lambda app: order.get(app["app_label"], 99))

    def index(self, request, extra_context=None):
        today = timezone.localdate()
        month_start = today.replace(day=1)
        access = {
            "orders": request.user.has_perm("orders.view_order"),
            "products": request.user.has_perm("catalog.view_product"),
            "messages": request.user.has_perm("core.view_contactmessage"),
            "customers": request.user.has_perm("auth.view_user"),
            "add_product": request.user.has_perm("catalog.add_product"),
        }
        order_queryset = Order.objects.all() if access["orders"] else Order.objects.none()
        product_queryset = Product.objects.all() if access["products"] else Product.objects.none()
        completed = order_queryset.exclude(status="cancelled")
        monthly = completed.filter(created_at__date__gte=month_start)
        extra_context = {
            **(extra_context or {}),
            "dashboard_access": access,
            "dashboard_stats": {
                "orders_today": order_queryset.filter(created_at__date=today).count(),
                "pending_orders": order_queryset.filter(status__in=("pending", "confirmed", "processing")).count(),
                "monthly_revenue": monthly.aggregate(value=Sum("total"))["value"] or 0,
                "active_products": product_queryset.filter(is_active=True).count(),
                "low_stock": product_queryset.filter(is_active=True, stock_quantity__lte=5).count(),
                "customers": User.objects.filter(is_staff=False).count() if access["customers"] else 0,
                "unread_messages": ContactMessage.objects.filter(is_read=False).count() if access["messages"] else 0,
            },
            "recent_orders": order_queryset.select_related("user").order_by("-created_at")[:7],
            "low_stock_products": product_queryset.filter(is_active=True, stock_quantity__lte=5).order_by("stock_quantity")[:6],
        }
        for order in extra_context["recent_orders"]:
            order.dashboard_status = CHOICE_LABELS.get(order.status, order.get_status_display())
        return super().index(request, extra_context)


rocks_admin_site = RocksAdminSite(name="rocks_admin")


class ArabicUserAdmin(ArabicAdminMixin, UserAdmin):
    pass


class ArabicGroupAdmin(ArabicAdminMixin, GroupAdmin):
    pass


class ArabicCategoryAdmin(ArabicAdminMixin, CategoryAdmin):
    search_fields = ("name", "name_ar", "description", "description_ar")


class ArabicProductImageInline(ArabicAdminMixin, ProductImageInline):
    pass


class ArabicProductSpecificationInline(ArabicAdminMixin, ProductSpecificationInline):
    pass


class ArabicProductVariantInline(ArabicAdminMixin, ProductVariantInline):
    pass


class ArabicProductAdmin(ArabicAdminMixin, ProductAdmin):
    list_per_page = 30
    save_on_top = True
    inlines = (ArabicProductImageInline, ArabicProductSpecificationInline, ArabicProductVariantInline)
    actions = ("activate_selected", "deactivate_selected", "feature_selected")
    search_fields = ("name", "name_ar", "sku", "description", "description_ar")

    ProductAdmin.thumbnail.short_description = "الصورة"

    @admin.action(description="تفعيل المنتجات المحددة")
    def activate_selected(self, request, queryset):
        self.message_user(request, f"تم تفعيل {queryset.update(is_active=True)} منتج.")

    @admin.action(description="إيقاف المنتجات المحددة")
    def deactivate_selected(self, request, queryset):
        self.message_user(request, f"تم إيقاف {queryset.update(is_active=False)} منتج.")

    @admin.action(description="إضافة المنتجات المحددة إلى المنتجات المميزة")
    def feature_selected(self, request, queryset):
        self.message_user(request, f"تم تمييز {queryset.update(is_featured=True)} منتج.")


class ArabicOrderItemInline(ArabicAdminMixin, OrderItemInline):
    pass


class ArabicOrderAdmin(ArabicAdminMixin, OrderAdmin):
    list_display = ("order_number", "customer_name", "phone", "total", "status_ar", "notification_ar", "created_at")
    list_per_page = 30
    list_filter = (OrderStatusFilter, PaymentStatusFilter, "created_at")
    date_hierarchy = "created_at"
    save_on_top = True
    inlines = (ArabicOrderItemInline,)
    readonly_fields = (
        "order_number", "public_token", "checkout_token", "subtotal", "shipping_cost",
        "discount", "total", "stock_restored", "created_at", "updated_at",
    )

    @admin.display(description="حالة الطلب", ordering="status")
    def status_ar(self, obj):
        return CHOICE_LABELS.get(obj.status, obj.get_status_display())

    @admin.display(description="حالة الإشعار")
    def notification_ar(self, obj):
        try:
            return CHOICE_LABELS.get(obj.notification.status, obj.notification.get_status_display())
        except OrderNotification.DoesNotExist:
            return "لم يُنشأ"


class ArabicNotificationAdmin(ArabicAdminMixin, OrderNotificationAdmin):
    list_display = ("order", "status_ar", "attempts", "last_attempt_at", "sent_at")
    list_filter = (NotificationStatusFilter,)

    OrderNotificationAdmin.retry_selected.short_description = "إعادة محاولة إرسال الإشعارات المحددة"

    @admin.display(description="الحالة", ordering="status")
    def status_ar(self, obj):
        return CHOICE_LABELS.get(obj.status, obj.get_status_display())

    @admin.action(description="إعادة محاولة إرسال الإشعارات المحددة")
    def retry_selected(self, request, queryset):
        sent = sum(1 for item in queryset if send_order_notifications(item.order_id))
        self.message_user(request, f"تم إرسال {sent} من أصل {queryset.count()} إشعار.")


class ArabicSiteSettingsAdmin(ArabicAdminMixin, SiteSettingsAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)


class ArabicContactAdmin(ArabicAdminMixin, ContactMessageAdmin):
    readonly_fields = ("name", "phone", "email", "subject", "message", "created_at")
    actions = ("mark_read", "mark_unread")

    @admin.action(description="تعليم الرسائل المحددة كمقروءة")
    def mark_read(self, request, queryset):
        self.message_user(request, f"تم تحديث {queryset.update(is_read=True)} رسالة.")

    @admin.action(description="تعليم الرسائل المحددة كغير مقروءة")
    def mark_unread(self, request, queryset):
        self.message_user(request, f"تم تحديث {queryset.update(is_read=False)} رسالة.")


class ArabicBannerAdmin(ArabicAdminMixin, BannerAdmin):
    save_on_top = True
    list_filter = (BannerLocationFilter, "is_active")


class ArabicSubscriberAdmin(ArabicAdminMixin, SubscriberAdmin):
    actions = ("activate_selected", "deactivate_selected")

    @admin.action(description="تفعيل المشتركين المحددين")
    def activate_selected(self, request, queryset):
        self.message_user(request, f"تم تفعيل {queryset.update(is_active=True)} مشترك.")

    @admin.action(description="إيقاف المشتركين المحددين")
    def deactivate_selected(self, request, queryset):
        self.message_user(request, f"تم إيقاف {queryset.update(is_active=False)} مشترك.")


class BasicArabicAdmin(ArabicAdminMixin, admin.ModelAdmin):
    list_per_page = 30


class ArabicAddressAdmin(BasicArabicAdmin):
    list_display = ("recipient_name", "user", "phone", "governorate", "city", "is_default")
    list_filter = ("governorate", "is_default")
    search_fields = ("recipient_name", "phone", "user__username", "user__email")


class ArabicProductAttributeAdmin(BasicArabicAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "name_ar", "slug")
    prepopulated_fields = {"slug": ("name",)}


class ArabicProductImageAdmin(BasicArabicAdmin):
    list_display = ("product", "alt_text", "sort_order")
    search_fields = ("product__name", "product__name_ar", "alt_text", "alt_text_ar")
    autocomplete_fields = ("product",)


class ArabicProductSpecificationAdmin(BasicArabicAdmin):
    list_display = ("product", "name", "value", "sort_order")
    search_fields = ("product__name", "product__name_ar", "name", "name_ar", "value", "value_ar")
    autocomplete_fields = ("product",)


class ArabicProductVariantAdmin(BasicArabicAdmin):
    list_display = ("product", "label", "sku", "price", "stock_quantity", "is_active")
    list_filter = ("is_active",)
    search_fields = ("product__name", "product__name_ar", "label", "label_ar", "sku")
    autocomplete_fields = ("product",)


class ArabicCouponAdmin(BasicArabicAdmin):
    list_display = ("code", "discount_type", "value", "minimum_order", "usage_count", "usage_limit", "is_active", "end_date")
    list_filter = (DiscountTypeFilter, "is_active")
    search_fields = ("code",)
    readonly_fields = ("usage_count",)


class ArabicShippingZoneAdmin(BasicArabicAdmin):
    list_display = ("name", "shipping_cost", "free_shipping_threshold", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "name_ar")
    ordering = ("sort_order", "name")


MANAGED_MODELS = (
    User, Group, Address, Category, Product, ProductAttribute, ProductImage,
    ProductSpecification, ProductVariant, Order, OrderItem, Coupon, ShippingZone,
    OrderNotification, SiteSettings, ContactMessage, Banner, Subscriber,
)
for model in MANAGED_MODELS:
    model_name = model._meta.model_name
    if model_name in MODEL_LABELS:
        model._meta.verbose_name = MODEL_LABELS[model_name]
        model._meta.verbose_name_plural = MODEL_LABELS[model_name]
    for field in model._meta.fields:
        if field.name in FIELD_LABELS:
            field.verbose_name = FIELD_LABELS[field.name]


rocks_admin_site.register(User, ArabicUserAdmin)
rocks_admin_site.register(Group, ArabicGroupAdmin)
rocks_admin_site.register(Address, ArabicAddressAdmin)
rocks_admin_site.register(Category, ArabicCategoryAdmin)
rocks_admin_site.register(Product, ArabicProductAdmin)
rocks_admin_site.register(ProductAttribute, ArabicProductAttributeAdmin)
rocks_admin_site.register(ProductImage, ArabicProductImageAdmin)
rocks_admin_site.register(ProductSpecification, ArabicProductSpecificationAdmin)
rocks_admin_site.register(ProductVariant, ArabicProductVariantAdmin)
rocks_admin_site.register(Order, ArabicOrderAdmin)
rocks_admin_site.register(Coupon, ArabicCouponAdmin)
rocks_admin_site.register(ShippingZone, ArabicShippingZoneAdmin)
rocks_admin_site.register(OrderNotification, ArabicNotificationAdmin)
rocks_admin_site.register(SiteSettings, ArabicSiteSettingsAdmin)
rocks_admin_site.register(ContactMessage, ArabicContactAdmin)
rocks_admin_site.register(Banner, ArabicBannerAdmin)
rocks_admin_site.register(Subscriber, ArabicSubscriberAdmin)
