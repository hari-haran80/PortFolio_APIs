from rest_framework import permissions

class IsOwnerOrSuperUser(permissions.BasePermission):
    """
    Custom permission: allow users to edit/delete their own review,
    and allow superusers to edit/delete any review.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_superuser
