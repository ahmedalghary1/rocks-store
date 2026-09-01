import hashlib
import logging
from xml.etree import ElementTree as ET

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connection, transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Category, Product
from marketing.models import Banner, Subscriber
from .forms import ContactForm, NewsletterForm

logger = logging.getLogger(__name__)


def _rate_key(request, action):
    identity = request.META.get("REMOTE_ADDR", "unknown")
    digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
    return f"rate:{action}:{digest}"


def home(request):
    products = Product.objects.filter(is_active=True, category__is_active=True).select_related("category").prefetch_related("variants")
    categories = Category.objects.filter(is_active=True, parent__isnull=True).annotate(
        active_product_count=Count("products", filter=Q(products__is_active=True))
    )[:6]
    now = timezone.now()
    banner = Banner.objects.filter(is_active=True).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now),
        Q(end_date__isnull=True) | Q(end_date__gte=now),
    ).first()
    return render(request, "core/home.html", {
        "categories": categories,
        "featured_products": products.filter(is_featured=True)[:8],
        "best_sellers": products.filter(is_best_seller=True)[:4],
        "new_products": products.filter(is_new=True)[:8],
        "marketing_banner": banner,
    })


def about(request):
    return render(request, "core/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            if not cache.add(_rate_key(request, "contact"), True, timeout=60):
                form.add_error(None, "انتظر دقيقة قبل إرسال رسالة أخرى.")
            else:
                contact_message = form.save()
                if settings.ORDER_NOTIFICATION_EMAIL:
                    transaction.on_commit(lambda: _notify_contact(contact_message.pk))
                messages.success(request, "وصلت رسالتك، وسيتواصل معك فريق ROCKS قريبًا.")
                return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def _notify_contact(message_id):
    from .models import ContactMessage
    item = ContactMessage.objects.get(pk=message_id)
    try:
        send_mail(
            f"رسالة تواصل: {item.subject}",
            f"الاسم: {item.name}\nالهاتف: {item.phone}\nالبريد: {item.email}\n\n{item.message}",
            settings.DEFAULT_FROM_EMAIL, [settings.ORDER_NOTIFICATION_EMAIL], fail_silently=False,
        )
    except Exception:
        logger.exception("Could not send contact notification %s", message_id)


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if not form.is_valid():
        messages.error(request, "أدخل بريدًا إلكترونيًا صحيحًا.")
    elif not cache.add(_rate_key(request, "newsletter"), True, timeout=30):
        messages.error(request, "انتظر قليلًا قبل المحاولة مرة أخرى.")
    else:
        subscriber, created = Subscriber.objects.get_or_create(email=form.cleaned_data["email"].lower())
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=("is_active",))
        messages.success(request, "تم اشتراكك بنجاح." if created else "هذا البريد مشترك بالفعل.")
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("core:home")


def wishlist(request):
    ids = request.session.get("wishlist", [])[:100]
    products = Product.objects.filter(id__in=ids, is_active=True, category__is_active=True).select_related("category")
    return render(request, "core/wishlist.html", {"products": products})


@require_POST
def wishlist_toggle(request, product_id):
    get_object_or_404(Product, pk=product_id, is_active=True, category__is_active=True)
    wishlist = list(dict.fromkeys(request.session.get("wishlist", [])))[:100]
    if product_id in wishlist:
        wishlist.remove(product_id)
        active = False
    else:
        if len(wishlist) >= 100:
            return JsonResponse({"ok": False, "message": "وصلت القائمة إلى الحد الأقصى."}, status=400)
        wishlist.append(product_id)
        active = True
    request.session["wishlist"] = wishlist
    return JsonResponse({"ok": True, "active": active, "count": len(wishlist)})


def sitemap(request):
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}urlset")

    def add_url(path, lastmod=None):
        node = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(node, f"{{{namespace}}}loc").text = request.build_absolute_uri(path)
        if lastmod:
            ET.SubElement(node, f"{{{namespace}}}lastmod").text = lastmod.date().isoformat()

    for path in ("/", "/products/", "/about/", "/contact/", "/privacy/", "/terms/", "/shipping-policy/", "/returns-policy/"):
        add_url(path)
    for product in Product.objects.filter(is_active=True, category__is_active=True):
        add_url(product.get_absolute_url(), product.updated_at)
    return HttpResponse(ET.tostring(root, encoding="unicode"), content_type="application/xml")


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok"})
    except Exception:
        logger.exception("Health check failed")
        return JsonResponse({"status": "unavailable"}, status=503)


def legal_page(request, template_name):
    return render(request, template_name)


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
