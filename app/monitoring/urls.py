from django.urls import path
from . import views

urlpatterns = [
    path("alerts/", views.list_alerts, name="list-alerts"),
    path("alerts/<int:pk>/resolve/", views.resolve_alert, name="resolve-alert"),
    path("agent/run/", views.run_agent, name="run-agent"),
    path("logs/", views.list_activity_logs, name="activity-logs"),
    path("blocked-ips/", views.list_blocked_ips, name="blocked-ips"),
    path("blocked-ips/unblock/", views.unblock_ip, name="unblock-ip"),
]