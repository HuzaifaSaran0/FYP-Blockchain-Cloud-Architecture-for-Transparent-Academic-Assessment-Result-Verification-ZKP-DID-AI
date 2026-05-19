from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    def ready(self):
        import sys
        # Only start scheduler in actual server process, not management commands
        cmd = " ".join(sys.argv)
        if any(x in cmd for x in ["makemigrations", "migrate", "shell", "collectstatic", "test"]):
            return
        self._start_agent_scheduler()

    def _start_agent_scheduler(self):
        import threading
        import time

        def run_periodically():
            # Wait 30s after startup before first run — lets DB fully initialize
            time.sleep(30)
            while True:
                try:
                    from monitoring.agent import ExamMonitoringAgent
                    ExamMonitoringAgent().run()
                except Exception:
                    pass
                time.sleep(300)

        t = threading.Thread(target=run_periodically, daemon=True)
        t.start()