"""Canonical URLs and safely serialized, factual search metadata."""
import json

from django.conf import settings
from django.urls import translate_url
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe


BRAND_ALIASES = ["ROCKS", "ROCKS EV", "روكس", "روكس الوسام", "وركس الوسام", "ROCKS ELWSAM"]


def absolute_url(request, path):
    if path.startswith(("https://", "http://")):
        return path
    origin = settings.SITE_URL or f"{request.scheme}://{request.get_host()}"
    return origin.rstrip("/") + "/" + path.lstrip("/")


def language_urls(request, path=None):
    path = path or request.path
    return {code: absolute_url(request, translate_url(path, code)) for code in ("en", "ar")}


def json_ld(value):
    # JSON escaping, rather than escapejs, keeps localized decimals and quotes valid.
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return mark_safe(payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def breadcrumbs_schema(request, category=None, product=None):
    from django.urls import reverse
    arabic = translation.get_language() == "ar"
    crumbs = [("الرئيسية" if arabic else "Home", reverse("core:home")),
              ("المنتجات" if arabic else "Products", reverse("catalog:list"))]
    if category:
        crumbs.append((category.display_name, category.get_absolute_url()))
    if product:
        crumbs.append((product.display_name, product.get_absolute_url()))
    return json_ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": position, "name": name, "item": absolute_url(request, path)}
        for position, (name, path) in enumerate(crumbs, 1)
    ]})


def store_schema(request, site, image):
    root = absolute_url(request, "/")
    store = {
        "@type": "OnlineStore", "@id": root + "#store",
        "name": site.company_name if site else "ROCKS ELWSAM",
        "alternateName": BRAND_ALIASES, "url": root, "logo": image,
        "areaServed": {"@type": "Country", "name": "Egypt"},
    }
    if site:
        for field, key in (("phone", "telephone"), ("email", "email")):
            if getattr(site, field):
                store[key] = getattr(site, field)
        if site.display_address:
            store["address"] = {"@type": "PostalAddress", "streetAddress": site.display_address, "addressCountry": "EG"}
        same_as = [getattr(site, field) for field in ("facebook", "instagram", "tiktok") if getattr(site, field)]
        if same_as:
            store["sameAs"] = same_as
    return {"@context": "https://schema.org", "@graph": [store, {
        "@type": "WebSite", "@id": root + "#website", "url": root,
        "name": "ROCKS ELWSAM | روكس الوسام", "alternateName": BRAND_ALIASES,
        "inLanguage": ["ar-EG", "en"], "publisher": {"@id": root + "#store"},
    }]}


def product_schema(request, product):
    from .models import SiteSettings
    site = SiteSettings.objects.first()
    currency = site.currency if site else "EGP"
    url = absolute_url(request, product.get_absolute_url())
    data = {
        "@context": "https://schema.org", "@type": "Product", "@id": url + "#product",
        "name": product.display_name, "description": strip_tags(product.display_short_description or product.display_description),
        "sku": product.sku, "url": url, "category": product.category.display_name,
        "brand": {"@type": "Brand", "name": "ROCKS"},
    }
    images = ([product.main_image.url] if product.main_image else []) + [image.image.url for image in product.images.all() if image.image]
    if images:
        data["image"] = [absolute_url(request, image) for image in images]
    specs = [{"@type": "PropertyValue", "name": item.display_name, "value": item.display_value} for item in product.specifications.all()]
    if specs:
        data["additionalProperty"] = specs

    def offer(price, stock, sku):
        return {"@type": "Offer", "sku": sku, "price": str(price), "priceCurrency": currency,
                "url": url, "itemCondition": "https://schema.org/NewCondition",
                "availability": "https://schema.org/InStock" if stock else "https://schema.org/OutOfStock",
                "seller": {"@id": absolute_url(request, "/") + "#store"}}

    variants = [variant for variant in product.variants.all() if variant.is_active]
    if variants:
        offers = [offer(v.price if v.price is not None else product.price, v.stock_quantity > 0, v.sku)
                  for v in variants if v.price is not None or product.price is not None]
        if offers:
            data["offers"] = offers
    elif product.price is not None:
        data["offers"] = offer(product.price, product.stock_quantity > 0, product.sku)
    return json_ld(data)


FAQ = {
    "ar": [
        ("هل ROCKS وROCKS EV وروكس ووركس الوسام تشير إلى المتجر نفسه؟", "نعم، ROCKS وROCKS EV وروكس هي أسماء تشير إلى متجر روكس الوسام (ROCKS ELWSAM) في مصر. ويمكن العثور عليه أيضًا بصيغة البحث «وركس الوسام». يضم المتجر كابلات شحن سيارات كهرباء وكابلات كهرباء ومشتركات، ويمكنك مراجعة المنتجات المتاحة ومواصفاتها قبل الطلب."),
        ("ما هو متجر روكس الوسام ROCKS ELWSAM؟", "روكس الوسام هو متجر ROCKS للمنتجات الكهربائية في مصر. يمكنك تصفح الكابلات والمشتركات الكهربائية والفيش والمفاتيح والإضاءة ومنتجات شحن السيارات، ومراجعة المنتجات المتاحة في الأقسام."),
        ("كيف أختار مشترك كهرباء مناسبًا؟", "راجع عدد المخارج وطول الكابل والمواصفات وحدود الاستخدام المعلنة لكل مشترك. قارنها باحتياجات أجهزتك، واسأل فريق روكس عن أي مواصفة غير واضحة قبل الطلب."),
        ("أين أجد أسعار كابلات الكهرباء ومشتركات روكس؟", "تظهر الأسعار المتاحة في صفحة كل منتج، وقد تختلف حسب الطول أو الخيار المحدد. إذا لم يظهر سعر، تواصل مع المتجر للاستفسار عن المنتج وتوفره."),
        ("كيف أختار كابلات شحن سيارات كهرباء من ROCKS EV؟", "عند مقارنة كابلات شحن السيارات الكهربائية، ابدأ بمتطلبات الشحن المحددة لسيارتك ومحطة الشحن، ثم راجع نوع الوصلات والقدرة والتيار وطول الكابل الموضح في صفحة المنتج. تواصل مع فريق روكس لتأكيد التوافق والتوفر قبل الطلب."),
        ("كيف أعرف تفاصيل الشحن والاسترجاع والضمان؟", "راجع صفحات سياسة الشحن والاسترجاع، وقسم الضمان في صفحة المنتج. تواصل مع خدمة العملاء لتأكيد تفاصيل الطلب والتوصيل."),
    ],
    "en": [
        ("Are ROCKS, ROCKS EV and روكس the same store?", "ROCKS, ROCKS EV and روكس refer to the ROCKS ELWSAM (روكس الوسام) store in Egypt. The store can also be found using the Arabic search spelling وركس الوسام. Browse EV charging cables, electrical cables and power strips, and check each product's availability and specifications before ordering."),
        ("What is ROCKS ELWSAM (روكس الوسام)?", "ROCKS ELWSAM is the ROCKS electrical products store in Egypt. Browse cables, power strips, plugs, switches, lighting and EV charging products, and check the categories for available products."),
        ("How do I choose a power strip?", "Check the number of outlets, cable length, specifications and stated usage limits for each power strip. Compare these with your devices and ask the ROCKS team about any unclear specification before ordering."),
        ("Where can I find ROCKS cable and power strip prices?", "Available prices appear on each product page and may vary by length or selected option. If a price is not displayed, contact the store to ask about the product and availability."),
        ("How do I choose ROCKS EV charging cables?", "Start with the charging requirements specified for your car and charging station, then check the connector type, power rating, current rating and cable length on the product page. Contact ROCKS to confirm compatibility and availability before ordering."),
        ("Where can I check shipping, returns and warranty details?", "Read the shipping and returns policy pages and the warranty section on the product page. Contact customer support to confirm order and delivery details."),
    ],
}


def faq_context():
    items = FAQ["ar" if translation.get_language() == "ar" else "en"]
    return {"store_faq": items, "faq_json_ld": json_ld({
        "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in items
        ],
    })}
