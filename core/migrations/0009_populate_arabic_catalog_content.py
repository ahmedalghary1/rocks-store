from django.db import migrations


PRODUCTS = {
    "modern-single-switch": ("مفتاح مفرد عصري من ROCKS", "مفتاح دقيق وآمن بتصميم عصري أنيق."),
    "schuko-socket": ("بريزة شوكو محمية من ROCKS", "توصيلة آمنة مزودة بحماية مدمجة للأطفال."),
    "led-bulb-12w": ("لمبة ليد 12 وات", "إضاءة بيضاء مريحة باستهلاك منخفض للطاقة."),
    "led-bulb-18w": ("لمبة ليد 18 وات", "إضاءة قوية وعمر تشغيلي طويل للمساحات الكبيرة."),
    "ceiling-light-24w": ("وحدة إضاءة سقف دائرية 24 وات", "وحدة نحيفة توزع إضاءة محايدة ومتساوية."),
    "outdoor-wall-light": ("مصباح حائط خارجي بمعيار IP65", "مصباح متين ومقاوم للعوامل الجوية للمداخل والواجهات."),
    "power-strip-4": ("مشترك كهربائي بـ 4 مخارج", "أربعة مخارج ومفتاح رئيسي وكابل يتحمل الاستخدام الشاق."),
    "power-strip-usb": ("مشترك كهربائي USB بـ 6 مخارج", "ستة مخارج ومنفذا USB في مشترك كهربائي واحد موثوق."),
    "cable-reel-20m": ("بكرة كابل 20 مترًا", "كابل مرن يتحمل الاستخدام الشاق على بكرة عملية للاستخدام اليومي."),
    "junction-box-10": ("علبة توصيل محكمة 10×10", "علبة محكمة ومتينة لتركيبات نظيفة ومنظمة."),
    "voltage-tester": ("قلم اختبار جهد احترافي", "كشف سريع وآمن للجهد مع مقبض معزول."),
    "insulated-screwdrivers": ("طقم مفكات معزولة من 6 قطع", "مفكات معزولة دقيقة بالمقاسات الأساسية."),
}

SPECIFICATION_NAMES = {"Voltage": "الجهد", "Material": "الخامة", "Warranty": "الضمان"}
SPECIFICATION_VALUES = {
    "220–240 V": "220–240 فولت",
    "Heat-resistant materials": "خامات مقاومة للحرارة",
    "One year from ROCKS": "عام من روكس",
}

GOVERNORATES = {
    "Cairo": "القاهرة", "Giza": "الجيزة", "Alexandria": "الإسكندرية", "Dakahlia": "الدقهلية",
    "Red Sea": "البحر الأحمر", "Beheira": "البحيرة", "Fayoum": "الفيوم", "Gharbia": "الغربية",
    "Ismailia": "الإسماعيلية", "Monufia": "المنوفية", "Minya": "المنيا", "Qalyubia": "القليوبية",
    "New Valley": "الوادي الجديد", "Suez": "السويس", "Aswan": "أسوان", "Assiut": "أسيوط",
    "Beni Suef": "بني سويف", "Port Said": "بورسعيد", "Damietta": "دمياط", "Sharqia": "الشرقية",
    "South Sinai": "جنوب سيناء", "Kafr El Sheikh": "كفر الشيخ", "Matrouh": "مطروح", "Luxor": "الأقصر",
    "Qena": "قنا", "North Sinai": "شمال سيناء", "Sohag": "سوهاج",
}


def populate_arabic_content(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    ProductSpecification = apps.get_model("catalog", "ProductSpecification")
    ShippingZone = apps.get_model("orders", "ShippingZone")

    for slug, (name_ar, short_description_ar) in PRODUCTS.items():
        product = Product.objects.filter(slug=slug).first()
        if not product:
            continue
        changed = []
        values = {
            "name_ar": name_ar,
            "short_description_ar": short_description_ar,
            "description_ar": f"{name_ar} مصمم وفق معايير روكس للجودة والأمان، باستخدام خامات مختارة بعناية لأداء يومي موثوق.",
            "meta_title_ar": f"{name_ar} | روكس",
            "meta_description_ar": short_description_ar,
        }
        for field, value in values.items():
            if not getattr(product, field):
                setattr(product, field, value)
                changed.append(field)
        if changed:
            product.save(update_fields=changed)

    for english, arabic in SPECIFICATION_NAMES.items():
        ProductSpecification.objects.filter(name=english, name_ar="").update(name_ar=arabic)
    for english, arabic in SPECIFICATION_VALUES.items():
        ProductSpecification.objects.filter(value=english, value_ar="").update(value_ar=arabic)
    for english, arabic in GOVERNORATES.items():
        ShippingZone.objects.filter(name=english, name_ar="").update(name_ar=arabic)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_category_seo_fields"),
        ("core", "0008_fix_bilingual_footer_text"),
        ("orders", "0007_bilingual_order_content"),
    ]

    operations = [migrations.RunPython(populate_arabic_content, migrations.RunPython.noop)]
