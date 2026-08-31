from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Category, Product, ProductSpecification
from core.models import SiteSettings
from orders.models import Coupon
from django.utils import timezone
from datetime import timedelta


CATEGORIES = [
    ("مفاتيح وبرايز", "switches-sockets", "toggle-left"), ("الإضاءة", "lighting", "lamp"),
    ("لمبات LED", "led", "lightbulb"), ("وصلات كهربائية", "cables", "cable"),
    ("علب التوصيل", "junction-boxes", "box"), ("أدوات الكهرباء", "tools", "wrench"),
    ("المشتركات", "power-strips", "plug"), ("ملحقات الكهرباء", "accessories", "settings"),
]
PRODUCTS = [
    ("مفتاح ROCKS مودرن مفرد", "modern-single-switch", "RK-SW-101", "switches-sockets", 185, 220, "لمسة دقيقة وآمنة بتصميم عصري يناسب المساحات الحديثة."),
    ("بريزة ROCKS شوكو بحماية", "schuko-socket", "RK-SK-210", "switches-sockets", 260, 300, "توصيل ثابت مع غطاء حماية داخلي للأطفال."),
    ("لمبة LED قدرة 12 وات", "led-bulb-12w", "RK-LED-12", "led", 95, 115, "إضاءة بيضاء مريحة واستهلاك منخفض للطاقة."),
    ("لمبة LED قدرة 18 وات", "led-bulb-18w", "RK-LED-18", "led", 135, 160, "إضاءة قوية بعمر تشغيل طويل للمساحات الواسعة."),
    ("كشاف سقف دائري 24 وات", "ceiling-light-24w", "RK-CL-24", "lighting", 490, 560, "كشاف نحيف بتوزيع ضوء متجانس ولون محايد."),
    ("أبليك خارجي مقاوم للماء", "outdoor-wall-light", "RK-OW-08", "lighting", 780, 890, "هيكل متين وحماية IP65 للمداخل والواجهات."),
    ("مشترك كهربائي 4 مخارج", "power-strip-4", "RK-PS-04", "power-strips", 425, 480, "أربعة مخارج مع مفتاح فصل وكابل عالي التحمل."),
    ("مشترك كهربائي 6 مخارج USB", "power-strip-usb", "RK-PS-USB", "power-strips", 720, 820, "حل طاقة متكامل بستة مخارج ومنفذي USB."),
    ("بكرة سلك 20 متر", "cable-reel-20m", "RK-CR-20", "cables", 1150, 1290, "سلك مرن عالي التحمل على بكرة عملية للاستخدام اليومي."),
    ("علبة توصيل محكمة 10×10", "junction-box-10", "RK-JB-10", "junction-boxes", 85, None, "علبة توصيل قوية بغطاء محكم للتركيبات المنظمة."),
    ("قلم اختبار كهرباء احترافي", "voltage-tester", "RK-TL-01", "tools", 120, 145, "كشف سريع وآمن للجهد بقبضة معزولة."),
    ("طقم مفكات معزولة 6 قطع", "insulated-screwdrivers", "RK-TL-06", "tools", 620, 700, "مفكات دقيقة بعزل قوي وأحجام أساسية للفني."),
]


class Command(BaseCommand):
    help = "إضافة بيانات عرض عربية لمتجر ROCKS"

    @transaction.atomic
    def handle(self, *args, **options):
        SiteSettings.objects.update_or_create(pk=1, defaults={"company_name": "ROCKS ELECTRIC", "footer_text": "قوة موثوقة لكل توصيلة.", "shipping_message": "شحن مجاني للطلبات فوق 1500 ج.م"})
        now = timezone.now()
        Coupon.objects.update_or_create(code="ROCKS10", defaults={"discount_type": "percentage", "value": 10, "minimum_order": 500, "start_date": now - timedelta(days=1), "end_date": now + timedelta(days=365), "usage_limit": 500, "is_active": True})
        category_map = {}
        for index, (name, slug, icon) in enumerate(CATEGORIES):
            category_map[slug], _ = Category.objects.update_or_create(slug=slug, defaults={"name": name, "icon": icon, "sort_order": index, "is_active": True})
        for index, (name, slug, sku, category, price, old_price, short) in enumerate(PRODUCTS):
            product, _ = Product.objects.update_or_create(slug=slug, defaults={
                "name": name, "sku": sku, "category": category_map[category], "short_description": short,
                "description": f"صُمم {name} وفق معايير ROCKS للجودة والثبات، مع خامات مختارة وأداء يعتمد عليه في الاستخدام اليومي.",
                "price": Decimal(price), "old_price": Decimal(old_price) if old_price else None, "stock_quantity": 20 + index,
                "is_featured": index < 8, "is_best_seller": index in {0, 2, 6, 8}, "is_new": index >= 8, "is_active": True,
                "meta_title": f"{name} | ROCKS ELECTRIC", "meta_description": short,
            })
            specs = [("الجهد", "220–240 فولت"), ("الخامة", "خامات مقاومة للحرارة"), ("الضمان", "عام من ROCKS")]
            for pos, (spec_name, value) in enumerate(specs):
                ProductSpecification.objects.update_or_create(product=product, name=spec_name, defaults={"value": value, "sort_order": pos})
        self.stdout.write(self.style.SUCCESS("ROCKS demo data is ready."))
