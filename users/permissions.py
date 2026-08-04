from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users with role='admin'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_role)


class IsFacultyRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_faculty)


class IsStudentRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsFacultyOrAdmin(BasePermission):
    """Common pattern: faculty manage their own courses, admins manage everything."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and (request.user.is_faculty or request.user.is_admin_role)
        )