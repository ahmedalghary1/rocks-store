from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Address
from api.serializers.auth import (
    AddressSerializer,
    ChangePasswordSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(tags=["Authentication & Account"])
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = RegisterSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Authentication & Account"])
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(tags=["Authentication & Account"])
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been updated successfully."}, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(tags=["Addresses"], description="List user saved delivery addresses"),
    create=extend_schema(tags=["Addresses"], description="Create a new saved delivery address"),
    retrieve=extend_schema(tags=["Addresses"], description="Retrieve address details"),
    update=extend_schema(tags=["Addresses"], description="Update delivery address"),
    partial_update=extend_schema(tags=["Addresses"], description="Partially update delivery address"),
    destroy=extend_schema(tags=["Addresses"], description="Delete saved delivery address"),
)
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.none()
    serializer_class = AddressSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    @extend_schema(tags=["Addresses"], description="Set address as default delivery address")
    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        address = self.get_object()
        Address.objects.filter(user=request.user).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
        serializer = self.get_serializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)
