from decimal import Decimal
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.service import Cart
from api.serializers.cart import (
    AddToCartSerializer,
    ApplyCouponSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)


def _get_cart(request):
    if not hasattr(request, "session") or request.session is None:
        request.session = request._request.session
    if not request.session.session_key:
        request.session.save()
    return Cart(request)


def _serialize_cart(cart, request):
    items = []
    for item in cart.items():
        product = item["product"]
        variant = item["variant"]
        image_url = None
        if product.main_image:
            image_url = request.build_absolute_uri(product.main_image.url)
        items.append({
            "key": item["key"],
            "product_id": product.id,
            "product_name": product.name,
            "product_name_ar": product.name_ar,
            "display_product_name": product.display_name,
            "product_slug": product.slug,
            "product_image": image_url,
            "variant_id": variant.id if variant else None,
            "variant_label": variant.label if variant else None,
            "variant_label_ar": variant.label_ar if variant else None,
            "display_variant_label": variant.display_label if variant else None,
            "sku": item["sku"],
            "price": item["price"],
            "quantity": item["quantity"],
            "stock_quantity": item["stock_quantity"],
            "total": item["total"],
        })

    coupon_data = None
    if cart.coupon:
        coupon_data = {
            "code": cart.coupon.code,
            "discount_type": cart.coupon.discount_type,
            "value": cart.coupon.value,
            "discount_amount": cart.discount,
        }

    return {
        "items": items,
        "count": cart.count,
        "subtotal": cart.subtotal,
        "shipping": cart.shipping,
        "free_shipping_threshold": Decimal(settings.FREE_SHIPPING_THRESHOLD),
        "coupon": coupon_data,
        "discount": cart.discount,
        "total": cart.total,
    }


@extend_schema(tags=["Shopping Cart"])
class CartView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(description="Retrieve current shopping cart items, subtotal, shipping, and totals", responses=CartSerializer)
    def get(self, request):
        cart = _get_cart(request)
        data = _serialize_cart(cart, request)
        serializer = CartSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Shopping Cart"])
class CartItemsView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description="Add a product or variant to shopping cart",
        request=AddToCartSerializer,
        responses=CartSerializer,
    )
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = _get_cart(request)
        product_id = serializer.validated_data["product_id"]
        variant_id = serializer.validated_data.get("variant_id")
        quantity = serializer.validated_data.get("quantity", 1)

        try:
            cart.add(product_id=product_id, quantity=quantity, variant_id=variant_id)
        except ValueError as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Shopping Cart"])
class CartItemDetailView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description="Update cart item quantity by item key (e.g. '1' or '1:2'). Set quantity=0 to remove.",
        request=UpdateCartItemSerializer,
        responses=CartSerializer,
    )
    def patch(self, request, item_key):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = _get_cart(request)
        quantity = serializer.validated_data["quantity"]

        try:
            cart.update(item_key, quantity)
        except ValueError as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Remove item from shopping cart by item key",
        responses=CartSerializer,
    )
    def delete(self, request, item_key):
        cart = _get_cart(request)
        cart.remove(item_key)
        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Shopping Cart"])
class CartCouponView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description="Apply discount coupon code to current cart",
        request=ApplyCouponSerializer,
        responses=CartSerializer,
    )
    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = _get_cart(request)
        code = serializer.validated_data["code"]

        applied = cart.apply_coupon(code)
        if not applied:
            return Response(
                {"detail": "Invalid coupon code, or coupon conditions (e.g. minimum spend or expiration) not met."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Remove applied coupon from cart",
        responses=CartSerializer,
    )
    def delete(self, request):
        cart = _get_cart(request)
        cart.remove_coupon()
        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Shopping Cart"])
class CartClearView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description="Empty the shopping cart completely",
        request=None,
        responses=CartSerializer,
    )
    def post(self, request):
        cart = _get_cart(request)
        cart.clear()
        data = _serialize_cart(cart, request)
        return Response(CartSerializer(data).data, status=status.HTTP_200_OK)

