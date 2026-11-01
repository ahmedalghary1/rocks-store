import django_filters
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Category, HomepageProduct, Product
from marketing.models import Banner
from api.serializers.catalog import (
    CategorySerializer,
    HomepageResponseSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)
from api.serializers.marketing import BannerSerializer


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    is_featured = django_filters.BooleanFilter(field_name="is_featured")
    is_best_seller = django_filters.BooleanFilter(field_name="is_best_seller")
    is_new = django_filters.BooleanFilter(field_name="is_new")
    is_coming_soon = django_filters.BooleanFilter(field_name="is_coming_soon")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = [
            "category",
            "min_price",
            "max_price",
            "is_featured",
            "is_best_seller",
            "is_new",
            "is_coming_soon",
            "in_stock",
        ]

    def filter_in_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(is_coming_soon=False).filter(
                Q(variants__isnull=True, stock_quantity__gt=0)
                | Q(variants__is_active=True, variants__stock_quantity__gt=0)
            ).distinct()
        if value is False:
            return queryset.filter(
                Q(is_coming_soon=True)
                | (Q(stock_quantity=0) & ~Q(variants__is_active=True, variants__stock_quantity__gt=0))
            ).distinct()
        return queryset


@extend_schema_view(
    list=extend_schema(tags=["Catalog: Categories"], description="List all active product categories"),
    retrieve=extend_schema(tags=["Catalog: Categories"], description="Retrieve category details by slug"),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .annotate(products_count=Count("products", filter=Q(products__is_active=True)))
            .order_by("sort_order", "name")
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Catalog: Products"],
        description="Search, filter, order, and paginate active products",
        parameters=[
            OpenApiParameter(name="category", description="Category slug", required=False, type=str),
            OpenApiParameter(name="search", description="Search by name, SKU, or description", required=False, type=str),
            OpenApiParameter(name="ordering", description="Ordering (e.g. -created_at, price, -price, name)", required=False, type=str),
            OpenApiParameter(name="in_stock", description="Filter by availability", required=False, type=bool),
            OpenApiParameter(name="min_price", description="Minimum price filter", required=False, type=float),
            OpenApiParameter(name="max_price", description="Maximum price filter", required=False, type=float),
        ],
    ),
    retrieve=extend_schema(tags=["Catalog: Products"], description="Retrieve product full details, gallery images, specifications, and variants by slug"),
)
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    permission_classes = (permissions.AllowAny,)
    filterset_class = ProductFilter
    search_fields = ("name", "name_ar", "sku", "short_description", "short_description_ar")
    ordering_fields = ("created_at", "price", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, category__is_active=True)
            .select_related("category", "specification_template", "warranty_template")
            .prefetch_related("images", "specifications", "variants")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @extend_schema(
        tags=["Catalog: Products"],
        description="Quick autocomplete suggestions for search bar (returns top matching products)",
        parameters=[OpenApiParameter(name="q", description="Query keyword", required=True, type=str)],
    )
    @action(detail=False, methods=["get"], url_path="suggest")
    def suggest(self, request):
        query = request.GET.get("q", "").strip()[:80]
        if len(query) < 2:
            return Response({"results": []})
        matches = (
            Product.objects.filter(is_active=True, category__is_active=True)
            .filter(Q(name__icontains=query) | Q(name_ar__icontains=query) | Q(sku__icontains=query))
            .select_related("category")[:6]
        )
        data = [
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "slug": p.slug,
                "sku": p.sku,
                "price": str(p.price) if p.price is not None else None,
                "category_name": p.category.display_name,
                "image_url": request.build_absolute_uri(p.main_image.url) if p.main_image else None,
            }
            for p in matches
        ]
        return Response({"results": data})


@extend_schema(
    tags=["Catalog: Products"],
    description="Homepage showcased data (hero banner and curated homepage products)",
    responses=HomepageResponseSerializer,
)
class HomepageView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        now = timezone.now()
        hero_banner = (
            Banner.objects.filter(is_active=True, location="hero")
            .filter(Q(start_date__isnull=True) | Q(start_date__lte=now))
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=now))
            .first()
        )

        homepage_placements = (
            HomepageProduct.objects.filter(
                is_active=True,
                product__is_active=True,
                product__category__is_active=True,
            )
            .select_related("product__category")
            .prefetch_related("product__variants")
            .order_by("sort_order", "pk")
        )

        if homepage_placements.exists():
            products = [item.product for item in homepage_placements[:12]]
        else:
            products = list(
                Product.objects.filter(is_active=True, category__is_active=True, is_featured=True)
                .select_related("category")
                .prefetch_related("variants")
                .order_by("-created_at")[:8]
            )

        products_data = ProductListSerializer(products, many=True, context={"request": request}).data
        banner_data = BannerSerializer(hero_banner, context={"request": request}).data if hero_banner else None

        return Response({
            "hero_banner": banner_data,
            "featured_products": products_data,
        })
