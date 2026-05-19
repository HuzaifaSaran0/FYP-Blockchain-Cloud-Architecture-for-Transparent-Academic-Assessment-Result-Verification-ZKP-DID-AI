from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import AIAlert, ActivityLog
from .agent import ExamMonitoringAgent


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_agent(request):
    """Manually trigger the monitoring agent."""
    try:
        agent = ExamMonitoringAgent()
        agent.run()
        return Response({"message": "Agent analysis complete."})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_alerts(request):
    alerts = AIAlert.objects.all().order_by("-triggered_at")[:50]
    data = [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "description": a.description,
            "is_resolved": a.is_resolved,
            "triggered_at": a.triggered_at,
            "resolved_at": a.resolved_at,
        }
        for a in alerts
    ]
    return Response({"results": data, "count": len(data)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_alert(request, pk):
    try:
        alert = AIAlert.objects.get(pk=pk)
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({"message": "Alert resolved."})
    except AIAlert.DoesNotExist:
        return Response({"error": "Alert not found."}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_activity_logs(request):
    logs = ActivityLog.objects.all().order_by("-timestamp")[:100]
    data = [
        {
            "id": l.id,
            "action": l.action,
            "performed_by": l.performed_by,
            "ip_address": l.ip_address,
            "timestamp": l.timestamp,
            "extra_data": l.extra_data,
        }
        for l in logs
    ]
    return Response({"results": data, "count": len(data)})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unblock_ip(request):
    ip = request.data.get("ip_address")
    if not ip:
        return Response({"error": "ip_address required."}, status=400)
    from monitoring.models import BlockedIP
    BlockedIP.objects.filter(ip_address=ip, is_active=True).update(is_active=False)
    return Response({"message": f"{ip} has been unblocked."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_blocked_ips(request):
    from monitoring.models import BlockedIP
    from django.utils import timezone
    blocks = BlockedIP.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    )
    data = [
        {
            "ip_address": b.ip_address,
            "reason": b.reason,
            "blocked_at": b.blocked_at,
            "expires_at": b.expires_at,
        }
        for b in blocks
    ]
    return Response({"results": data, "count": len(data)})