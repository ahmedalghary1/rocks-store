from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to anyone,
    but require staff status for write operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Object-level permission to allow owners of an object or staff members to access/edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        user = getattr(obj, "user", None)
        return user is not None and user == request.user

