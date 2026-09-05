from django.db import migrations


CATEGORY_NAMES = {
    "switches-sockets": "Switches & Sockets",
    "lighting": "Lighting",
    "led": "LED Lamps",
    "cables": "Electrical Cables",
    "junction-boxes": "Junction Boxes",
    "tools": "Electrical Tools",
    "power-strips": "Power Strips",
    "accessories": "Electrical Accessories",
}

PRODUCT_CONTENT = {
    "modern-single-switch": ("ROCKS Modern Single Switch", "A precise, safe switch with a clean modern profile."),
    "schuko-socket": ("ROCKS Protected Schuko Socket", "A secure connection with integrated child protection."),
    "led-bulb-12w": ("12W LED Lamp", "Comfortable white light with low energy consumption."),
    "led-bulb-18w": ("18W LED Lamp", "Powerful illumination and long service life for larger spaces."),
    "ceiling-light-24w": ("24W Round Ceiling Light", "A slim fixture with even, neutral light distribution."),
    "outdoor-wall-light": ("IP65 Outdoor Wall Light", "A durable, weather-resistant light for entrances and facades."),
    "power-strip-4": ("4-Outlet Power Strip", "Four outlets, a master switch, and a heavy-duty cable."),
    "power-strip-usb": ("6-Outlet USB Power Strip", "Six outlets and two USB ports in one dependable power hub."),
    "cable-reel-20m": ("20m Cable Reel", "A flexible, heavy-duty cable on a practical everyday reel."),
    "junction-box-10": ("10×10 Sealed Junction Box", "A durable sealed box for clean, organized installations."),
    "voltage-tester": ("Professional Voltage Tester", "Fast, safe voltage detection with an insulated grip."),
    "insulated-screwdrivers": ("6-Piece Insulated Screwdriver Set", "Precision insulated screwdrivers in essential sizes."),
}

GOVERNORATES = {
    "القاهرة": "Cairo", "الجيزة": "Giza", "الإسكندرية": "Alexandria",
    "الدقهلية": "Dakahlia", "البحر الأحمر": "Red Sea", "البحيرة": "Beheira",
    "الفيوم": "Fayoum", "الغربية": "Gharbia", "الإسماعيلية": "Ismailia",
    "المنوفية": "Monufia", "المنيا": "Minya", "القليوبية": "Qalyubia",
    "الوادي الجديد": "New Valley", "السويس": "Suez", "أسوان": "Aswan",
    "أسيوط": "Assiut", "بني سويف": "Beni Suef", "بورسعيد": "Port Said",
    "دمياط": "Damietta", "الشرقية": "Sharqia", "جنوب سيناء": "South Sinai",
    "كفر الشيخ": "Kafr El Sheikh", "مطروح": "Matrouh", "الأقصر": "Luxor",
    "قنا": "Qena", "شمال سيناء": "North Sinai", "سوهاج": "Sohag",
}


def translate_content(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    ProductSpecification = apps.get_model("catalog", "ProductSpecification")
    ProductVariant = apps.get_model("catalog", "ProductVariant")
    ShippingZone = apps.get_model("orders", "ShippingZone")
    Address = apps.get_model("accounts", "Address")

    SiteSettings.objects.update(
        company_name="ROCKS EV Charging Solutions",
        footer_text="Powering a cleaner tomorrow.",
        shipping_message="Fast delivery across Egypt",
        currency="EGP",
    )
    SiteSettings.objects.filter(address="القاهرة، مصر").update(address="Cairo, Egypt")

    for slug, name in CATEGORY_NAMES.items():
        Category.objects.filter(slug=slug).update(name=name)

    for slug, (name, short_description) in PRODUCT_CONTENT.items():
        Product.objects.filter(slug=slug).update(
            name=name,
            short_description=short_description,
            description=f"{name} is engineered to ROCKS quality and safety standards, using carefully selected materials for dependable everyday performance.",
            meta_title=f"{name} | ROCKS",
            meta_description=short_description,
        )

    specification_names = {"الجهد": "Voltage", "الخامة": "Material", "الضمان": "Warranty"}
    specification_values = {
        "220–240 فولت": "220–240 V",
        "خامات مقاومة للحرارة": "Heat-resistant materials",
        "عام من ROCKS": "One year from ROCKS",
    }
    for old, new in specification_names.items():
        ProductSpecification.objects.filter(name=old).update(name=new)
    for old, new in specification_values.items():
        ProductSpecification.objects.filter(value=old).update(value=new)

    variant_labels = {"أبيض": "White", "أسود": "Black", "كبير": "Large", "صغير": "Small"}
    for old, new in variant_labels.items():
        ProductVariant.objects.filter(label=old).update(label=new)

    for old, new in GOVERNORATES.items():
        ShippingZone.objects.filter(name=old).update(name=new)

    Address.objects.filter(label="المنزل").update(label="Home")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_address_label"),
        ("catalog", "0004_alter_category_options"),
        ("core", "0005_alter_sitesettings_options_and_more"),
        ("orders", "0006_alter_coupon_discount_type_and_more"),
    ]

    operations = [migrations.RunPython(translate_content, migrations.RunPython.noop)]
