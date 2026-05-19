import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class ExamMonitoringAgent:
    """
    Agentic AI monitoring agent.
    Autonomously analyzes system activity logs and generates alerts
    based on predefined rules and anomaly thresholds.
    """

    # Thresholds
    FAILED_LOGIN_THRESHOLD = 5       # alerts if >5 failed logins in 10 mins
    BULK_RESULT_THRESHOLD = 20       # alerts if >20 results published in 5 mins
    SUSPICIOUS_IP_THRESHOLD = 3      # alerts if same IP triggers >3 failed logins
    INACTIVITY_WINDOW_HOURS = 24     # alerts if no activity for 24hrs during exam period

    def __init__(self):
        from monitoring.models import ActivityLog, AIAlert
        self.ActivityLog = ActivityLog
        self.AIAlert = AIAlert
        self.now = timezone.now()

    def run(self):
        """Entry point — runs all checks autonomously."""
        logger.info("🤖 ExamMonitoringAgent: starting analysis cycle...")
        self._check_failed_logins()
        self._check_bulk_result_publish()
        self._check_suspicious_ip()
        self._check_exam_activity()
        logger.info("✅ ExamMonitoringAgent: analysis cycle complete.")

    def _create_alert(self, alert_type, severity, description):
        """Creates alert only if same type not already open."""
        exists = self.AIAlert.objects.filter(
            alert_type=alert_type,
            is_resolved=False,
            triggered_at__gte=self.now - timedelta(hours=1),
        ).exists()
        if not exists:
            self.AIAlert.objects.create(
                alert_type=alert_type,
                severity=severity,
                description=description,
            )
            logger.warning(f"🚨 Alert created: [{severity.upper()}] {alert_type}")

    def _check_failed_logins(self):
        """Detects brute force login attempts."""
        window = self.now - timedelta(minutes=10)
        logs = self.ActivityLog.objects.filter(
            action__icontains="failed login",
            timestamp__gte=window,
            ip_address__isnull=False,
        )
        count = logs.count()
        if count >= self.FAILED_LOGIN_THRESHOLD:
            self._create_alert(
                alert_type="Brute Force Login Attempt",
                severity="high",
                description=(
                    f"{count} failed login attempts detected within the last 10 minutes. "
                    f"Originating IPs have been automatically blocked for 30 minutes."
                ),
            )
            # Block all IPs involved
            ips = logs.values_list("ip_address", flat=True).distinct()
            for ip in ips:
                self._block_ip(ip, f"Brute force — {count} failed logins in 10 mins")

    def _check_bulk_result_publish(self):
        """Detects abnormally high result publishing rate."""
        window = self.now - timedelta(minutes=5)
        count = self.ActivityLog.objects.filter(
            action__icontains="result published",
            timestamp__gte=window,
        ).count()
        if count >= self.BULK_RESULT_THRESHOLD:
            self._create_alert(
                alert_type="Bulk Result Publication Anomaly",
                severity="medium",
                description=(
                    f"{count} results published within 5 minutes. "
                    f"This exceeds normal thresholds and may indicate automated manipulation."
                ),
            )

    def _block_ip(self, ip_address, reason):
        """Temporarily blocks an IP for 30 minutes."""
        from monitoring.models import BlockedIP
        from datetime import timedelta
        expires = self.now + timedelta(minutes=30)
        BlockedIP.objects.update_or_create(
            ip_address=ip_address,
            defaults={
                "reason": reason,
                "expires_at": expires,
                "is_active": True,
            }
        )
        logger.warning(f"🔒 IP {ip_address} blocked until {expires}")

    def _check_suspicious_ip(self):
        """Detects repeated failed actions from same IP and blocks it."""
        from django.db.models import Count
        window = self.now - timedelta(minutes=15)
        suspicious = (
            self.ActivityLog.objects.filter(
                action__icontains="failed",
                timestamp__gte=window,
                ip_address__isnull=False,
            )
            .values("ip_address")
            .annotate(total=Count("id"))
            .filter(total__gte=self.SUSPICIOUS_IP_THRESHOLD)
        )
        for entry in suspicious:
            self._create_alert(
                alert_type="Suspicious IP Activity",
                severity="high",
                description=(
                    f"IP address {entry['ip_address']} triggered "
                    f"{entry['total']} failed actions in 15 minutes. "
                    f"IP has been automatically blocked for 30 minutes."
                ),
            )
            # Auto-block the IP
            self._block_ip(
                ip_address=entry["ip_address"],
                reason=f"{entry['total']} failed attempts in 15 minutes"
            )

    def _check_exam_activity(self):
        """Detects if no activity logged during an active exam period."""
        from examination.models import Exam
        ongoing = Exam.objects.filter(status="ongoing").exists()
        if not ongoing:
            return
        window = self.now - timedelta(hours=self.INACTIVITY_WINDOW_HOURS)
        recent = self.ActivityLog.objects.filter(
            timestamp__gte=window
        ).exists()
        if not recent:
            self._create_alert(
                alert_type="System Inactivity During Exam",
                severity="medium",
                description=(
                    f"No system activity recorded in the last "
                    f"{self.INACTIVITY_WINDOW_HOURS} hours while an exam is ongoing. "
                    f"Possible system or monitoring failure."
                ),
            )