from collections import OrderedDict

from django.contrib.auth.models import Group, User

from accounts.models import Address
from catalog.models import Category, HomepageProduct, Product, ProductAttribute, ProductImage, ProductSpecification, ProductVariant
from core.models import ContactMessage, SiteSettings
from marketing.models import Banner, Subscriber
from orders.models import Coupon, Order, OrderItem, OrderNotification, ShippingZone


RESOURCES = OrderedDict({
    "orders": {"model": Order, "label": "الطلبات", "singular": "طلب", "icon": "shopping-bag", "group": "sales", "list": ("order_number", "customer_name", "phone", "total", "status", "payment_status", "created_at"), "search": ("order_number", "customer_name", "phone", "email"), "filters": ("status", "payment_status"), "select": ("user", "coupon")},
    "order-items": {"model": OrderItem, "label": "عناصر الطلبات", "singular": "عنصر طلب", "icon": "package", "group": "sales", "list": ("order", "product_name", "sku", "price", "quantity", "total"), "search": ("order__order_number", "product_name", "sku"), "filters": ("order",), "select": ("order", "product", "variant")},
    "coupons": {"model": Coupon, "label": "كوبونات الخصم", "singular": "كوبون", "icon": "ticket-percent", "group": "sales", "list": ("code", "discount_type", "value", "minimum_order", "usage_count", "usage_limit", "is_active"), "search": ("code",), "filters": ("discount_type", "is_active")},
    "shipping-zones": {"model": ShippingZone, "label": "مناطق الشحن", "singular": "منطقة شحن", "icon": "truck", "group": "sales", "list": ("name", "name_ar", "shipping_cost", "free_shipping_threshold", "is_active", "sort_order"), "search": ("name", "name_ar"), "filters": ("is_active",)},
    "notifications": {"model": OrderNotification, "label": "إشعارات الطلبات", "singular": "إشعار طلب", "icon": "bell-ring", "group": "sales", "list": ("order", "status", "attempts", "last_attempt_at", "sent_at"), "search": ("order__order_number", "last_error"), "filters": ("status",), "select": ("order",)},

    "products": {"model": Product, "label": "المنتجات", "singular": "منتج", "icon": "package-open", "group": "catalog", "list": ("main_image", "name", "sku", "category", "price", "stock_quantity", "is_active", "updated_at"), "search": ("name", "name_ar", "sku", "description", "description_ar"), "filters": ("category", "is_active", "is_featured", "is_best_seller", "is_new"), "select": ("category",)},
    "homepage-products": {"model": HomepageProduct, "label": "منتجات الصفحة الرئيسية", "singular": "منتج في الرئيسية", "icon": "gallery-thumbnails", "group": "catalog", "list": ("product", "sort_order", "is_active"), "search": ("product__name", "product__name_ar", "product__sku"), "filters": ("is_active",), "select": ("product",)},
    "categories": {"model": Category, "label": "التصنيفات", "singular": "تصنيف", "icon": "layout-grid", "group": "catalog", "list": ("image", "name", "name_ar", "parent", "is_active", "sort_order"), "search": ("name", "name_ar", "description", "description_ar"), "filters": ("parent", "is_active"), "select": ("parent",)},
    "variants": {"model": ProductVariant, "label": "خيارات المنتجات", "singular": "خيار منتج", "icon": "boxes", "group": "catalog", "list": ("product", "label", "sku", "price", "stock_quantity", "is_active"), "search": ("product__name", "label", "label_ar", "sku"), "filters": ("product", "is_active"), "select": ("product",)},
    "product-images": {"model": ProductImage, "label": "صور المنتجات", "singular": "صورة منتج", "icon": "images", "group": "catalog", "list": ("image", "product", "alt_text", "sort_order"), "search": ("product__name", "alt_text", "alt_text_ar"), "filters": ("product",), "select": ("product",)},
    "specifications": {"model": ProductSpecification, "label": "مواصفات المنتجات", "singular": "مواصفة", "icon": "list-checks", "group": "catalog", "list": ("product", "name", "value", "sort_order"), "search": ("product__name", "name", "name_ar", "value", "value_ar"), "filters": ("product",), "select": ("product",)},
    "attributes": {"model": ProductAttribute, "label": "خصائص المنتجات", "singular": "خاصية", "icon": "sliders-horizontal", "group": "catalog", "list": ("name", "name_ar", "slug"), "search": ("name", "name_ar", "slug")},

    "site-settings": {"model": SiteSettings, "label": "إعدادات الموقع", "singular": "إعدادات الموقع", "icon": "settings", "group": "content", "list": ("company_name", "phone", "email", "currency"), "search": ("company_name", "phone", "email"), "singleton": True},
    "banners": {"model": Banner, "label": "البنرات الإعلانية", "singular": "بانر", "icon": "gallery-horizontal", "group": "content", "list": ("image", "title", "location", "is_active", "sort_order", "start_date", "end_date"), "search": ("title", "subtitle"), "filters": ("location", "is_active")},
    "messages": {"model": ContactMessage, "label": "رسائل التواصل", "singular": "رسالة", "icon": "messages-square", "group": "content", "list": ("name", "subject", "phone", "email", "created_at", "is_read"), "search": ("name", "phone", "email", "subject", "message"), "filters": ("is_read",)},
    "subscribers": {"model": Subscriber, "label": "مشتركو النشرة", "singular": "مشترك", "icon": "mail", "group": "content", "list": ("email", "is_active", "created_at"), "search": ("email",), "filters": ("is_active",)},

    "users": {"model": User, "label": "المستخدمون", "singular": "مستخدم", "icon": "users", "group": "people", "list": ("username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined"), "search": ("username", "email", "first_name", "last_name"), "filters": ("is_staff", "is_active")},
    "groups": {"model": Group, "label": "مجموعات الصلاحيات", "singular": "مجموعة صلاحيات", "icon": "shield-check", "group": "people", "list": ("name",), "search": ("name",)},
    "addresses": {"model": Address, "label": "عناوين العملاء", "singular": "عنوان عميل", "icon": "map-pin", "group": "people", "list": ("user", "label", "recipient_name", "phone", "governorate", "city", "is_default"), "search": ("user__username", "recipient_name", "phone", "governorate", "city"), "filters": ("is_default",), "select": ("user",)},
})

GROUPS = (
    ("sales", "المبيعات والطلبات"),
    ("catalog", "المنتجات والمخزون"),
    ("content", "الموقع والتسويق"),
    ("people", "العملاء والصلاحيات"),
)


FIELD_LABELS = {
    "name": "الاسم", "name_ar": "الاسم بالعربية", "title": "العنوان", "title_ar": "العنوان بالعربية", "subtitle": "العنوان الفرعي", "subtitle_ar": "العنوان الفرعي بالعربية",
    "slug": "الرابط المختصر", "description": "الوصف", "description_ar": "الوصف بالعربية",
    "short_description": "الوصف المختصر", "short_description_ar": "الوصف المختصر بالعربية",
    "category": "التصنيف", "parent": "التصنيف الرئيسي", "image": "الصورة", "main_image": "الصورة الرئيسية",
    "mobile_image": "صورة الهاتف", "alt_text": "النص البديل", "alt_text_ar": "النص البديل بالعربية",
    "icon": "الأيقونة", "sku": "رمز المنتج", "price": "السعر", "old_price": "السعر قبل الخصم",
    "stock_quantity": "الكمية بالمخزون", "is_active": "نشط", "is_featured": "مميز",
    "is_best_seller": "الأكثر مبيعًا", "is_new": "جديد", "sort_order": "ترتيب العرض",
    "meta_title": "عنوان محركات البحث", "meta_title_ar": "عنوان محركات البحث بالعربية",
    "meta_description": "وصف محركات البحث", "meta_description_ar": "وصف محركات البحث بالعربية",
    "product": "المنتج", "variant": "الخيار", "label": "التسمية", "label_ar": "التسمية بالعربية",
    "value": "القيمة", "value_ar": "القيمة بالعربية", "attributes": "الخصائص JSON",
    "order": "الطلب", "order_number": "رقم الطلب", "customer_name": "اسم العميل", "phone": "الهاتف",
    "second_phone": "هاتف بديل", "email": "البريد الإلكتروني", "governorate": "المحافظة", "city": "المدينة",
    "address": "العنوان", "address_ar": "العنوان بالعربية", "address_line": "العنوان التفصيلي",
    "notes": "ملاحظات", "subtotal": "إجمالي المنتجات", "shipping_cost": "تكلفة الشحن",
    "discount": "الخصم", "total": "الإجمالي", "status": "الحالة", "payment_method": "طريقة الدفع",
    "payment_status": "حالة الدفع", "coupon": "الكوبون", "product_name": "اسم المنتج وقت الطلب",
    "product_name_ar": "اسم المنتج بالعربية", "quantity": "الكمية", "code": "الكود",
    "discount_type": "نوع الخصم", "minimum_order": "الحد الأدنى للطلب", "start_date": "تاريخ البداية",
    "end_date": "تاريخ النهاية", "usage_limit": "حد الاستخدام", "usage_count": "مرات الاستخدام",
    "free_shipping_threshold": "حد الشحن المجاني", "attempts": "عدد المحاولات", "last_error": "آخر خطأ",
    "last_attempt_at": "آخر محاولة", "sent_at": "تاريخ الإرسال", "subject": "الموضوع", "message": "الرسالة",
    "is_read": "تمت القراءة", "company_name": "اسم الشركة", "whatsapp": "واتساب", "facebook": "فيسبوك",
    "instagram": "إنستجرام", "tiktok": "تيك توك", "footer_text": "نص التذييل",
    "footer_text_ar": "نص التذييل بالعربية", "shipping_message": "رسالة الشحن",
    "shipping_message_ar": "رسالة الشحن بالعربية", "currency": "العملة", "link": "الرابط",
    "button_text": "نص الزر", "button_text_ar": "نص الزر بالعربية", "location": "مكان الظهور", "recipient_name": "اسم المستلم",
    "is_default": "العنوان الافتراضي", "user": "المستخدم", "username": "اسم المستخدم",
    "first_name": "الاسم الأول", "last_name": "اسم العائلة", "is_staff": "موظف", "is_superuser": "مدير كامل",
    "groups": "مجموعات الصلاحيات", "user_permissions": "الصلاحيات المباشرة", "password": "كلمة المرور",
    "date_joined": "تاريخ الانضمام", "created_at": "تاريخ الإنشاء", "updated_at": "آخر تحديث",
}


CHOICE_LABELS = {
    "pending": "قيد المراجعة", "confirmed": "تم التأكيد", "processing": "قيد التجهيز", "shipped": "تم الشحن",
    "delivered": "تم التسليم", "cancelled": "ملغي", "unpaid": "غير مدفوع", "paid": "مدفوع",
    "refunded": "مسترد", "sending": "جارٍ الإرسال", "sent": "تم الإرسال", "failed": "فشل الإرسال",
    "skipped": "لا يوجد مستلمون", "cod": "الدفع عند الاستلام", "percentage": "نسبة مئوية",
    "fixed": "قيمة ثابتة", "hero": "واجهة الرئيسية", "offer": "عرض", "promo": "ترويجي",
}


def resource_for(key):
    return RESOURCES.get(key)


def permission_name(config, action):
    model = config["model"]
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"
