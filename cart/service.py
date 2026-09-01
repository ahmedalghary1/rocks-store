from decimal import Decimal

from django.conf import settings
from catalog.models import Product, ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault("cart", {})
        if not isinstance(self.data, dict):
            self.data = {}
            self.session["cart"] = self.data
            self.session.modified = True
        self._items_cache = None
        self._coupon_cache = None

    @staticmethod
    def _quantity(value):
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            raise ValueError("الكمية غير صالحة.")

    @staticmethod
    def _parse_key(key):
        parts = str(key).split(":", 1)
        try:
            return int(parts[0]), int(parts[1]) if len(parts) == 2 else None
        except (TypeError, ValueError):
            return None, None

    @staticmethod
    def make_key(product_id, variant_id=None):
        return f"{product_id}:{variant_id}" if variant_id else str(product_id)

    @staticmethod
    def _stored_quantity(value):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    def add(self, product_id, quantity=1, variant_id=None):
        product = Product.objects.get(pk=product_id, is_active=True)
        variant = None
        if variant_id:
            variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True)
        available = variant.stock_quantity if variant else product.stock_quantity
        if available <= 0:
            raise ValueError("هذا المنتج غير متوفر حاليًا.")
        key = self.make_key(product.id, variant.id if variant else None)
        current = self._stored_quantity(self.data.get(key, 0))
        self.data[key] = min(available, current + self._quantity(quantity))
        self._save()

    def update(self, item_key, quantity):
        product_id, variant_id = self._parse_key(item_key)
        if not product_id:
            raise ValueError("عنصر السلة غير صالح.")
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("الكمية غير صالحة.")
        if quantity <= 0:
            self.remove(item_key)
            return
        product = Product.objects.get(pk=product_id, is_active=True)
        variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True) if variant_id else None
        available = variant.stock_quantity if variant else product.stock_quantity
        if available <= 0:
            self.remove(item_key)
            raise ValueError("نفدت الكمية المتاحة من هذا المنتج.")
        self.data[str(item_key)] = min(available, quantity)
        self._save()

    def remove(self, item_key):
        self.data.pop(str(item_key), None)
        self._save()

    def clear(self):
        self.session["cart"] = {}
        self.session.pop("coupon_code", None)
        self.data = self.session["cart"]
        self._invalidate()
        self.session.modified = True

    def items(self):
        if self._items_cache is not None:
            return self._items_cache
        parsed = [(str(key), *self._parse_key(key)) for key in list(self.data)]
        product_ids = {product_id for _, product_id, variant_id in parsed if product_id and not variant_id}
        variant_ids = {variant_id for _, _, variant_id in parsed if variant_id}
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids, is_active=True).select_related("category")}
        variants = {v.id: v for v in ProductVariant.objects.filter(
            id__in=variant_ids, is_active=True, product__is_active=True
        ).select_related("product__category")}

        result, stale = [], []
        for key, product_id, variant_id in parsed:
            variant = variants.get(variant_id) if variant_id else None
            product = variant.product if variant else products.get(product_id)
            if not product or (variant and variant.product_id != product_id):
                stale.append(key)
                continue
            available = variant.stock_quantity if variant else product.stock_quantity
            quantity = min(self._stored_quantity(self.data.get(key, 0)), available)
            if quantity <= 0:
                stale.append(key)
                continue
            price = variant.price if variant and variant.price is not None else product.price
            result.append({
                "key": key, "product": product, "variant": variant,
                "sku": variant.sku if variant else product.sku,
                "price": price, "quantity": quantity, "stock_quantity": available,
                "total": price * quantity,
            })
        if stale:
            for key in stale:
                self.data.pop(key, None)
            self.session["cart"] = self.data
            self.session.modified = True
        self._items_cache = result
        return result

    @property
    def count(self):
        return sum(item["quantity"] for item in self.items())

    @property
    def subtotal(self):
        return sum((item["total"] for item in self.items()), Decimal("0"))

    @property
    def shipping(self):
        if not self.items() or self.subtotal >= Decimal(settings.FREE_SHIPPING_THRESHOLD):
            return Decimal("0")
        return Decimal(settings.CART_SHIPPING_COST)

    @property
    def coupon(self):
        if self._coupon_cache is not None:
            return self._coupon_cache or None
        from orders.models import Coupon
        code = self.session.get("coupon_code")
        self._coupon_cache = Coupon.objects.filter(code__iexact=code).first() if code else False
        return self._coupon_cache or None

    @property
    def discount(self):
        return self.coupon.discount_for(self.subtotal) if self.coupon else Decimal("0")

    @property
    def total(self):
        return max(Decimal("0"), self.subtotal + self.shipping - self.discount)

    def apply_coupon(self, code):
        from orders.models import Coupon
        coupon = Coupon.objects.filter(code__iexact=str(code).strip()).first()
        if not coupon or coupon.discount_for(self.subtotal) <= 0:
            return False
        self.session["coupon_code"] = coupon.code
        self._coupon_cache = coupon
        self.session.modified = True
        return True

    def remove_coupon(self):
        self.session.pop("coupon_code", None)
        self._coupon_cache = None
        self.session.modified = True

    def _invalidate(self):
        self._items_cache = None
        self._coupon_cache = None

    def _save(self):
        self._invalidate()
        self.session["cart"] = self.data
        self.session.modified = True
