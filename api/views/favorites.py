from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from accounts.models import Favorite
from api.pagination import StandardResultsSetPagination
from api.serializers.catalog import ProductListSerializer
from catalog.models import Product


@extend_schema_view(
    list=extend_schema(tags=["Favorites"], description="List the signed-in customer's favorite products", responses=ProductListSerializer(many=True)),
    create=extend_schema(tags=["Favorites"], description="Save an active product to favorites"),
    destroy=extend_schema(tags=["Favorites"], description="Remove a favorite by product ID"),
)
class FavoriteViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Product.objects.none()
    lookup_value_regex = "[0-9]+"
    serializer_class = ProductListSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request):
        products = Product.objects.filter(
            favorited_by__user=request.user, is_active=True, category__is_active=True
        ).select_related("category").prefetch_related("variants").order_by("-favorited_by__created_at")
        page = self.paginate_queryset(products)
        if page is not None:
            return self.get_paginated_response(ProductListSerializer(page, many=True, context={"request": request}).data)
        return Response(ProductListSerializer(products, many=True, context={"request": request}).data)

    @extend_schema(request={"application/json": {"type": "object", "properties": {"product_id": {"type": "integer"}}, "required": ["product_id"]}}, responses={201: ProductListSerializer, 200: ProductListSerializer})
    def create(self, request):
        try:
            product_id = int(request.data.get("product_id"))
        except (TypeError, ValueError):
            return Response({"product_id": ["A valid product ID is required."]}, status=status.HTTP_400_BAD_REQUEST)
        product = Product.objects.filter(pk=product_id, is_active=True, category__is_active=True).select_related("category").first()
        if not product:
            return Response({"product_id": ["Product not found."]}, status=status.HTTP_404_NOT_FOUND)
        _, created = Favorite.objects.get_or_create(user=request.user, product=product)
        return Response(ProductListSerializer(product, context={"request": request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        Favorite.objects.filter(user=request.user, product_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
