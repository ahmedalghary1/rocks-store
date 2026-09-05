from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Category, Product, ProductSpecification
from core.models import SiteSettings
from orders.models import Coupon


CATEGORIES = [
    ("Switches & Sockets", "switches-sockets", "toggle-left"),
    ("Lighting", "lighting", "lamp"),
    ("LED Lamps", "led", "lightbulb"),
    ("Electrical Cables", "cables", "cable"),
    ("Junction Boxes", "junction-boxes", "box"),
    ("Electrical Tools", "tools", "wrench"),
    ("Power Strips", "power-strips", "plug"),
    ("Electrical Accessories", "accessories", "settings"),
]

PRODUCTS = [
    ("ROCKS Modern Single Switch", "modern-single-switch", "RK-SW-101", "switches-sockets", 185, 220, "A precise, safe switch with a clean modern profile."),
    ("ROCKS Protected Schuko Socket", "schuko-socket", "RK-SK-210", "switches-sockets", 260, 300, "A secure connection with integrated child protection."),
    ("12W LED Lamp", "led-bulb-12w", "RK-LED-12", "led", 95, 115, "Comfortable white light with low energy consumption."),
    ("18W LED Lamp", "led-bulb-18w", "RK-LED-18", "led", 135, 160, "Powerful illumination and long service life for larger spaces."),
    ("24W Round Ceiling Light", "ceiling-light-24w", "RK-CL-24", "lighting", 490, 560, "A slim fixture with even, neutral light distribution."),
    ("IP65 Outdoor Wall Light", "outdoor-wall-light", "RK-OW-08", "lighting", 780, 890, "A durable, weather-resistant light for entrances and facades."),
    ("4-Outlet Power Strip", "power-strip-4", "RK-PS-04", "power-strips", 425, 480, "Four outlets, a master switch, and a heavy-duty cable."),
    ("6-Outlet USB Power Strip", "power-strip-usb", "RK-PS-USB", "power-strips", 720, 820, "Six outlets and two USB ports in one dependable power hub."),
    ("20m Cable Reel", "cable-reel-20m", "RK-CR-20", "cables", 1150, 1290, "A flexible, heavy-duty cable on a practical everyday reel."),
    ("10×10 Sealed Junction Box", "junction-box-10", "RK-JB-10", "junction-boxes", 85, None, "A durable sealed box for clean, organized installations."),
    ("Professional Voltage Tester", "voltage-tester", "RK-TL-01", "tools", 120, 145, "Fast, safe voltage detection with an insulated grip."),
    ("6-Piece Insulated Screwdriver Set", "insulated-screwdrivers", "RK-TL-06", "tools", 620, 700, "Precision insulated screwdrivers in essential sizes."),
]


class Command(BaseCommand):
    help = "Create professional English demo data for the ROCKS store"

    @transaction.atomic
    def handle(self, *args, **options):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                "company_name": "ROCKS EV Charging Solutions",
                "footer_text": "Powering a cleaner tomorrow.",
                "shipping_message": "Fast delivery across Egypt",
                "currency": "EGP",
            },
        )
        now = timezone.now()
        Coupon.objects.update_or_create(
            code="ROCKS10",
            defaults={
                "discount_type": "percentage",
                "value": 10,
                "minimum_order": 500,
                "start_date": now - timedelta(days=1),
                "end_date": now + timedelta(days=365),
                "usage_limit": 500,
                "is_active": True,
            },
        )

        category_map = {}
        for index, (name, slug, icon) in enumerate(CATEGORIES):
            category_map[slug], _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "icon": icon, "sort_order": index, "is_active": True},
            )

        for index, (name, slug, sku, category, price, old_price, short) in enumerate(PRODUCTS):
            product, _ = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "sku": sku,
                    "category": category_map[category],
                    "short_description": short,
                    "description": f"{name} is engineered to ROCKS quality and safety standards, using carefully selected materials for dependable everyday performance.",
                    "price": Decimal(price),
                    "old_price": Decimal(old_price) if old_price else None,
                    "stock_quantity": 20 + index,
                    "is_featured": index < 8,
                    "is_best_seller": index in {0, 2, 6, 8},
                    "is_new": index >= 8,
                    "is_active": True,
                    "meta_title": f"{name} | ROCKS",
                    "meta_description": short,
                },
            )
            specifications = [
                ("Voltage", "220–240 V"),
                ("Material", "Heat-resistant materials"),
                ("Warranty", "One year from ROCKS"),
            ]
            for position, (spec_name, value) in enumerate(specifications):
                ProductSpecification.objects.update_or_create(
                    product=product,
                    name=spec_name,
                    defaults={"value": value, "sort_order": position},
                )

        self.stdout.write(self.style.SUCCESS("ROCKS English demo data is ready."))
