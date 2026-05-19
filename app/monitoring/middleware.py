from django.http import JsonResponse
from django.utils import timezone


class IPBlockMiddleware:
    """
    Checks every incoming request against the BlockedIP table.
    Returns 403 if IP is actively blocked and block has not expired.
    Automatically deactivates expired blocks.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_ip(request)
        if ip and self._is_blocked(ip):
            return JsonResponse(
                {
                    "error": "Access temporarily blocked due to suspicious activity. "
                             "Please try again later."
                },
                status=403,
            )
        return self.get_response(request)

    def _get_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _is_blocked(self, ip):
        try:
            from monitoring.models import BlockedIP
            now = timezone.now()
            block = BlockedIP.objects.filter(
                ip_address=ip,
                is_active=True,
                expires_at__gt=now,
            ).first()
            if block:
                return True
            # Auto-expire old blocks silently
            BlockedIP.objects.filter(
                ip_address=ip,
                is_active=True,
                expires_at__lte=now,
            ).update(is_active=False)
            return False
        except Exception:
            return False