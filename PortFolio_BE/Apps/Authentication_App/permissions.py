from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Anyone can read; only staff/superusers can create, update or delete."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsSuperUser(permissions.BasePermission):
    """Only superusers (the portfolio owner). The FE admin dashboard is gated on is_superuser."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
