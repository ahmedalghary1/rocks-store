from django.db import migrations, models


CATEGORY_CONTENT = {
    "switches-sockets": {
        "name_ar": "المفاتيح والبرايز والفيش",
        "description": "Electrical switches, wall sockets and plugs designed for safe, reliable everyday connections at home or work.",
        "description_ar": "مفاتيح وبرايز وفيش كهرباء للاستخدام اليومي الآمن والموثوق في المنزل والعمل.",
        "meta_title": "Electrical Switches, Sockets & Plugs | ROCKS Egypt",
        "meta_title_ar": "مفاتيح وبرايز وفيش كهرباء | روكس مصر",
        "meta_description": "Shop electrical switches, sockets and plugs from ROCKS in Egypt. Clear specifications, dependable materials and delivery options.",
        "meta_description_ar": "تسوق مفاتيح وبرايز وفيش كهرباء من روكس في مصر بمواصفات واضحة وخامات موثوقة وخيارات توصيل.",
    },
    "lighting": {
        "name_ar": "الإضاءة والديكور",
        "description": "Practical indoor and outdoor lighting, including modern fixtures and decorative lighting solutions.",
        "description_ar": "حلول إضاءة داخلية وخارجية عملية تشمل وحدات الإضاءة الحديثة والدوايات الديكور.",
        "meta_title": "Lighting & Decorative Lamp Holders | ROCKS Egypt",
        "meta_title_ar": "إضاءة ودوايات ديكور | روكس مصر",
        "meta_description": "Discover ROCKS lighting and decorative lamp holder solutions for homes and businesses, with clear specifications and delivery in Egypt.",
        "meta_description_ar": "اكتشف إضاءة ودوايات ديكور روكس للمنازل والأعمال بمواصفات واضحة وتوصيل داخل مصر.",
    },
    "led": {
        "name_ar": "لمبات ليد",
        "description": "Energy-efficient LED lamps in practical wattages for comfortable, dependable everyday lighting.",
        "description_ar": "لمبات ليد موفرة للطاقة بقدرات عملية لإضاءة يومية مريحة وموثوقة.",
        "meta_title": "LED Lamps & Energy-Saving Bulbs | ROCKS Egypt",
        "meta_title_ar": "لمبات ليد موفرة للطاقة | روكس مصر",
        "meta_description": "Shop energy-saving ROCKS LED lamps in Egypt. Compare wattage, light output and specifications before you buy.",
        "meta_description_ar": "تسوق لمبات ليد روكس الموفرة للطاقة في مصر وقارن القدرة والإضاءة والمواصفات قبل الشراء.",
    },
    "cables": {
        "name_ar": "الكابلات الكهربائية وكابلات السيارات",
        "description": "Electrical cables, cable reels and EV charging cable solutions selected for safe, dependable power delivery.",
        "description_ar": "كابلات كهرباء وبكر كابلات وحلول كابلات شحن السيارات مختارة لتوصيل طاقة آمن وموثوق.",
        "meta_title": "Electrical & EV Charging Cables | ROCKS Egypt",
        "meta_title_ar": "كابلات كهرباء وشحن سيارات | روكس مصر",
        "meta_description": "Shop electrical cables, cable reels and EV charging cable solutions from ROCKS with clear compatibility and safety specifications.",
        "meta_description_ar": "تسوق كابلات الكهرباء وبكر الكابلات وكابلات شحن السيارات من روكس مع مواصفات توافق وأمان واضحة.",
    },
    "junction-boxes": {
        "name_ar": "علب التوصيل",
        "description": "Junction boxes for neat, protected and organized electrical installations.",
        "description_ar": "علب توصيل لتركيبات كهربائية منظمة ومحمية بمواصفات واضحة.",
        "meta_title": "Electrical Junction Boxes | ROCKS Egypt",
        "meta_title_ar": "علب توصيل كهرباء | روكس مصر",
        "meta_description": "Shop ROCKS electrical junction boxes for protected, organized installations with delivery options across Egypt.",
        "meta_description_ar": "تسوق علب توصيل الكهرباء من روكس لتركيبات محمية ومنظمة مع خيارات توصيل داخل مصر.",
    },
    "tools": {
        "name_ar": "أدوات الكهرباء",
        "description": "Electrical tools for safer testing, installation and everyday maintenance work.",
        "description_ar": "أدوات كهربائية للفحص والتركيب وأعمال الصيانة اليومية بصورة أكثر أمانًا.",
        "meta_title": "Electrical Tools & Testers | ROCKS Egypt",
        "meta_title_ar": "أدوات كهرباء وأجهزة فحص | روكس مصر",
        "meta_description": "Shop insulated electrical tools and voltage testers from ROCKS, with practical specifications and delivery in Egypt.",
        "meta_description_ar": "تسوق أدوات الكهرباء المعزولة وأجهزة فحص الجهد من روكس بمواصفات عملية وتوصيل داخل مصر.",
    },
    "power-strips": {
        "name_ar": "المشتركات الكهربائية",
        "description": "Power strips with practical outlet configurations, switches and USB options for everyday home and office use.",
        "description_ar": "مشتركات كهربائية بعدد مخارج عملي ومفاتيح وخيارات USB للاستخدام اليومي في المنزل والمكتب.",
        "meta_title": "Power Strips, Extensions & USB Outlets | ROCKS Egypt",
        "meta_title_ar": "مشتركات كهرباء ووصلات USB | روكس مصر",
        "meta_description": "Shop ROCKS power strips and electrical extensions in Egypt, including multiple outlets, switches and USB charging options.",
        "meta_description_ar": "تسوق مشتركات ووصلات الكهرباء من روكس في مصر بعدة مخارج ومفاتيح وخيارات شحن USB.",
    },
    "accessories": {
        "name_ar": "إكسسوارات الكهرباء",
        "description": "Useful electrical accessories for completing home, office and installation setups.",
        "description_ar": "إكسسوارات كهربائية عملية لاستكمال تجهيزات المنزل والمكتب وأعمال التركيب.",
        "meta_title": "Electrical Accessories | ROCKS Egypt",
        "meta_title_ar": "إكسسوارات كهربائية | روكس مصر",
        "meta_description": "Browse practical ROCKS electrical accessories for home, office and professional installation needs in Egypt.",
        "meta_description_ar": "تصفح إكسسوارات روكس الكهربائية العملية للمنزل والمكتب واحتياجات التركيب في مصر.",
    },
}


def add_category_content(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    for slug, content in CATEGORY_CONTENT.items():
        Category.objects.filter(slug=slug).update(**content)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_homepageproduct")]

    operations = [
        migrations.AddField(model_name="category", name="meta_description", field=models.CharField(blank=True, max_length=260)),
        migrations.AddField(model_name="category", name="meta_description_ar", field=models.CharField(blank=True, max_length=260, verbose_name="وصف محركات البحث بالعربية")),
        migrations.AddField(model_name="category", name="meta_title", field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name="category", name="meta_title_ar", field=models.CharField(blank=True, max_length=160, verbose_name="عنوان محركات البحث بالعربية")),
        migrations.RunPython(add_category_content, migrations.RunPython.noop),
    ]
