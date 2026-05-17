# core/permissions.py
import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)

class MethodPermissionMap(BasePermission):
    """
    Enforces permissions based on HTTP method, using a declarative map on the view.
    
    Usage:
        class MyView(APIView):
            permission_classes = [MethodPermissionMap]
            method_permission_map = {
                'GET': ['examination.view_exam'],
                'POST': ['examination.add_exam', 'examination.change_exam'],
                'DELETE': [],
            }
            permission_mode = 'all'  # or 'any'; defaults to 'all'
    """
    message = "You don't have permission to perform this action."

    def has_permission(self, request, view):
        # Anonymous users are handled by IsAuthenticated separately; but fail closed.
        if not request.user or not request.user.is_authenticated:
            return False

        method = request.method
        method_map = getattr(view, "method_permission_map", None)

        # Explicit map required – no guessing.
        if not isinstance(method_map, dict):
            logger.warning(f"View {view.__class__.__name__} missing method_permission_map")
            return False

        required_perms = method_map.get(method)
        if required_perms is None:
            # Method not mapped = forbidden (fail‑closed)
            return False

        if not required_perms:
            # Empty list means "no extra permissions required" (but user must be authenticated)
            return True

        permission_mode = getattr(view, "permission_mode", "all")
        checks = [request.user.has_perm(perm) for perm in required_perms]

        if permission_mode == "any":
            return any(checks)
        # Default to 'all'
        return all(checks)