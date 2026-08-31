from decimal import Decimal
from catalog.models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault("cart", {})

    def add(self, product_id, quantity=1):
        product = Product.objects.get(pk=product_id, is_active=True)
        key = str(product_id)
        current = int(self.data.get(key, 0))
        self.data[key] = min(product.stock_quantity, current + max(1, int(quantity)))
        self._save()

    def update(self, product_id, quantity):
        product = Product.objects.get(pk=product_id, is_active=True)
        quantity = int(quantity)
        if quantity <= 0:
            self.remove(product_id)
        else:
            self.data[str(product_id)] = min(product.stock_quantity, quantity)
            self._save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.session["cart"] = {}
        self.session.pop("coupon_code", None)
        self.data = self.session["cart"]
        self.session.modified = True

    def items(self):
        products = Product.objects.filter(id__in=self.data.keys(), is_active=True).select_related("category")
        result = []
        for product in products:
            quantity = min(int(self.data[str(product.id)]), product.stock_quantity)
            result.append({"product": product, "quantity": quantity, "total": product.price * quantity})
        return result

    @property
    def subtotal(self):
        return sum((item["total"] for item in self.items()), Decimal("0"))

    @property
    def shipping(self):
        return Decimal("0") if self.subtotal >= 1500 or not self.data else Decimal("75")

    @property
    def coupon(self):
        from orders.models import Coupon
        code = self.session.get("coupon_code")
        return Coupon.objects.filter(code__iexact=code).first() if code else None

    @property
    def discount(self):
        return self.coupon.discount_for(self.subtotal) if self.coupon else Decimal("0")

    @property
    def total(self):
        return max(Decimal("0"), self.subtotal + self.shipping - self.discount)

    def apply_coupon(self, code):
        from orders.models import Coupon
        coupon = Coupon.objects.filter(code__iexact=code.strip()).first()
        if not coupon or coupon.discount_for(self.subtotal) <= 0:
            return False
        self.session["coupon_code"] = coupon.code
        self.session.modified = True
        return True

    def remove_coupon(self):
        self.session.pop("coupon_code", None)
        self.session.modified = True

    def _save(self):
        self.session["cart"] = self.data
        self.session.modified = True
