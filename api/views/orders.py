import uuid
from decimal import Decimal
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.service import Cart
from catalog.models import Product, ProductVariant
from orders.forms import resolve_shipping_zone
from orders.models import Coupon, Order, OrderItem, OrderNotification, ShippingZone
from orders.services import send_order_notifications
from api.serializers.orders import (
    CouponValidateResponseSerializer,
    CouponValidateSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderTrackInputSerializer,
    OrderTrackResponseSerializer,
    ShippingZoneSerializer,
)


class ShippingZoneListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ShippingZoneSerializer
    pagination_class = None

    @extend_schema(tags=["Shipping & Checkout"], description="List all active delivery governorates and shipping rates")
    def get_queryset(self):
        return ShippingZone.objects.filter(is_active=True).order_by("sort_order", "name")


class ValidateCouponView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Shipping & Checkout"],
        description="Check if a coupon code is valid for a given subtotal",
        request=CouponValidateSerializer,
        responses=CouponValidateResponseSerializer,
    )
    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip()
        subtotal = serializer.validated_data["subtotal"]

        coupon = Coupon.objects.filter(code__iexact=code).first()
        now = timezone.now()

        if not coupon:
            return Response({
                "valid": False,
                "code": code,
                "discount_amount": Decimal("0.00"),
                "message": "Coupon code not found.",
            }, status=status.HTTP_404_NOT_FOUND)

        if not coupon.is_active or not (coupon.start_date <= now <= coupon.end_date):
            return Response({
                "valid": False,
                "code": code,
                "discount_amount": Decimal("0.00"),
                "message": "This coupon has expired or is inactive.",
            }, status=status.HTTP_400_BAD_REQUEST)

        if coupon.usage_count >= coupon.usage_limit:
            return Response({
                "valid": False,
                "code": code,
                "discount_amount": Decimal("0.00"),
                "message": "This coupon usage limit has been reached.",
            }, status=status.HTTP_400_BAD_REQUEST)

        if subtotal < coupon.minimum_order:
            return Response({
                "valid": False,
                "code": code,
                "discount_amount": Decimal("0.00"),
                "message": f"Minimum order for this coupon is {coupon.minimum_order} EGP.",
            }, status=status.HTTP_400_BAD_REQUEST)

        discount_amount = coupon.discount_for(subtotal)
        return Response({
            "valid": True,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "value": coupon.value,
            "discount_amount": discount_amount,
            "message": "Coupon is valid.",
        }, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Shipping & Checkout"],
        description="Place an order (Cash on delivery) with stock validation, coupon verification, and notification dispatch",
        request=OrderCreateSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = data.get("checkout_token") or uuid.uuid4()
        existing = Order.objects.filter(checkout_token=token).prefetch_related("items").first()
        if existing:
            if not self._same_customer(request, existing, data):
                return Response({"detail": "Checkout token is already in use."}, status=status.HTTP_409_CONFLICT)
            return Response(OrderSerializer(existing, context={"request": request}).data, status=status.HTTP_200_OK)

        raw_items = data.get("items")
        from_session_cart = False
        prepared_items = []

        if raw_items:
            # Direct items payload provided
            for raw in raw_items:
                product_id = raw["product_id"]
                variant_id = raw.get("variant_id")
                qty = raw.get("quantity", 1)

                try:
                    product = Product.objects.get(pk=product_id, is_active=True, category__is_active=True)
                except Product.DoesNotExist:
                    return Response({"detail": f"Product #{product_id} not found or inactive."}, status=status.HTTP_400_BAD_REQUEST)

                if product.is_coming_soon:
                    return Response({"detail": f"Product '{product.name}' is coming soon."}, status=status.HTTP_400_BAD_REQUEST)

                variant = None
                if variant_id:
                    try:
                        variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True)
                    except ProductVariant.DoesNotExist:
                        return Response({"detail": f"Variant #{variant_id} does not exist for product '{product.name}'."}, status=status.HTTP_400_BAD_REQUEST)
                elif product.variants.filter(is_active=True).exists():
                    return Response({"detail": f"Please select an option/variant for product '{product.name}'."}, status=status.HTTP_400_BAD_REQUEST)

                available = variant.stock_quantity if variant else product.stock_quantity
                if available < qty:
                    return Response({"detail": f"Insufficient stock for '{product.name}'. Available: {available}."}, status=status.HTTP_400_BAD_REQUEST)

                unit_price = variant.price if variant and variant.price is not None else product.price
                if unit_price is None:
                    return Response({"detail": f"Product '{product.name}' has no price configured."}, status=status.HTTP_400_BAD_REQUEST)

                prepared_items.append({
                    "product": product,
                    "variant": variant,
                    "sku": variant.sku if variant else product.sku,
                    "price": unit_price,
                    "quantity": qty,
                    "total": unit_price * qty,
                })
        else:
            # Use current session Cart
            from_session_cart = True
            cart = Cart(request)
            cart_items = cart.items()
            if not cart_items:
                return Response({"detail": "Shopping cart is empty. Provide items or add items to cart first."}, status=status.HTTP_400_BAD_REQUEST)

            for item in cart_items:
                prepared_items.append({
                    "product": item["product"],
                    "variant": item["variant"],
                    "sku": item["sku"],
                    "price": item["price"],
                    "quantity": item["quantity"],
                    "total": item["total"],
                })

        subtotal = sum((item["total"] for item in prepared_items), Decimal("0"))
        zone = serializer.shipping_zone
        shipping_cost = zone.cost_for(subtotal)

        # Coupon resolution
        coupon_code = data.get("coupon_code", "").strip()
        coupon = None
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if not coupon:
                return Response({"detail": "Coupon code is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        elif from_session_cart:
            cart = Cart(request)
            coupon = cart.coupon

        try:
            with transaction.atomic():
                discount = Decimal("0")
                claimed_coupon = None
                if coupon:
                    proposed = coupon.discount_for(subtotal)
                    if proposed <= 0:
                        raise ValueError("Coupon is expired, exhausted, or does not meet the minimum order.")
                    now = timezone.now()
                    claimed = Coupon.objects.filter(
                        pk=coupon.pk,
                        is_active=True,
                        start_date__lte=now,
                        end_date__gte=now,
                        usage_count__lt=F("usage_limit"),
                        minimum_order__lte=subtotal,
                    ).update(usage_count=F("usage_count") + 1)
                    if not claimed:
                        raise ValueError("Coupon is no longer available.")
                    discount = proposed
                    claimed_coupon = coupon

                # Atomically deduct stock
                for item in prepared_items:
                    stock_model = ProductVariant if item["variant"] else Product
                    target_pk = item["variant"].pk if item["variant"] else item["product"].pk
                    updated = stock_model.objects.filter(
                        pk=target_pk,
                        is_active=True,
                        stock_quantity__gte=item["quantity"],
                    ).update(stock_quantity=F("stock_quantity") - item["quantity"])
                    if updated != 1:
                        raise ValueError(f"Stock for '{item['product'].name}' is no longer sufficient.")

                order_number = f"RK-{timezone.now():%y%m%d}-{uuid.uuid4().hex[:12].upper()}"
                total = max(Decimal("0"), subtotal + shipping_cost - discount)

                user = request.user if request.user and request.user.is_authenticated else None

                order = Order.objects.create(
                    order_number=order_number,
                    checkout_token=token,
                    user=user,
                    coupon=claimed_coupon,
                    customer_name=data["customer_name"],
                    phone=data["phone"],
                    second_phone=data.get("second_phone", ""),
                    email=data.get("email", ""),
                    governorate=zone.name,
                    city=data["city"],
                    address=data["address"],
                    notes=data.get("notes", ""),
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    discount=discount,
                    total=total,
                    payment_method="cod",
                    payment_status="unpaid",
                    status="pending",
                )

                items_to_create = [
                    OrderItem(
                        order=order,
                        product=item["product"],
                        variant=item["variant"],
                        product_name=item["product"].name,
                        product_name_ar=item["product"].name_ar,
                        sku=item["sku"],
                        price=item["price"],
                        quantity=item["quantity"],
                        total=item["total"],
                    )
                    for item in prepared_items
                ]
                OrderItem.objects.bulk_create(items_to_create)
                OrderNotification.objects.create(order=order)

                order_id = order.pk
                transaction.on_commit(lambda: send_order_notifications(order_id))

        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            existing = Order.objects.filter(checkout_token=token).prefetch_related("items").first()
            if existing and self._same_customer(request, existing, data):
                return Response(OrderSerializer(existing, context={"request": request}).data, status=status.HTTP_200_OK)
            raise

        if from_session_cart:
            Cart(request).clear()

        # Set session last_order_token if session exists
        if hasattr(request, "session") and request.session:
            request.session["last_order_token"] = str(order.public_token)

        output = Order.objects.prefetch_related("items").get(pk=order.pk)
        return Response(OrderSerializer(output, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _same_customer(request, order, data):
        if order.user_id:
            return bool(request.user.is_authenticated and order.user_id == request.user.pk)
        return order.phone == data["phone"] and order.customer_name == data["customer_name"]


class OrderTrackView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Shipping & Checkout"],
        description="Publicly track order status by order number and phone number",
        request=OrderTrackInputSerializer,
        responses=OrderTrackResponseSerializer,
    )
    def post(self, request):
        serializer = OrderTrackInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_number = serializer.validated_data["order_number"].strip()
        phone = serializer.validated_data["phone"]

        order = Order.objects.filter(order_number__iexact=order_number, phone=phone).first()
        if not order:
            return Response({"detail": "No order found matching these details."}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderTrackResponseSerializer(order).data, status=status.HTTP_200_OK)


class PublicOrderReceiptView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Shipping & Checkout"],
        description="View order receipt and item breakdown by public UUID token",
        responses=OrderSerializer,
    )
    def get(self, request, public_token):
        order = get_object_or_404(Order.objects.prefetch_related("items"), public_token=public_token)
        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["User Orders"], description="List all past orders for the authenticated customer"),
    retrieve=extend_schema(tags=["User Orders"], description="Retrieve detailed order breakdown by order number"),
)
class UserOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderSerializer
    lookup_field = "order_number"
    queryset = Order.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).prefetch_related("items").order_by("-created_at")

