from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "face_recognition"

    def ready(self):
        # Skip warmup during management commands (migrations, shell, etc.)
        import sys
        if "runserver" in sys.argv or "gunicorn" in sys.argv[0:1]:
            return
        self._warmup()

    def _warmup(self):
        try:
            from .face_utils import warmup_model
            import threading
            # Run in background thread — doesn't block Django startup
            t = threading.Thread(target=warmup_model, daemon=True)
            t.start()
            logger.info("DeepFace warmup thread started.")
        except Exception as e:
            logger.warning(f"DeepFace warmup thread failed to start: {e}")