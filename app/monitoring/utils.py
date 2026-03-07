from django.utils import timezone


def log_activity(action: str, performed_by: str, request=None, extra_data: dict = None):
    """
    Utility to create an ActivityLog entry from anywhere in the codebase.
    Import lazily to avoid circular imports.
    """
    from monitoring.models import ActivityLog

    ip = None
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

    ActivityLog.objects.create(
        action=action,
        performed_by=performed_by,
        ip_address=ip,
        extra_data=extra_data or {},
    )
