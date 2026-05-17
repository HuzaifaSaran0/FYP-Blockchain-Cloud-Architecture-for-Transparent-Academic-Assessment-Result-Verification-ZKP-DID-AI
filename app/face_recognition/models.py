from django.db import models
import uuid
from django.utils import timezone


class FaceEncoding(models.Model):
    registration = models.OneToOneField(
        "examination.Registration",
        on_delete=models.CASCADE,
        related_name="face_encoding",
    )
    encoding_vector = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FaceEncoding — {self.registration.full_name}"


class CheckinLog(models.Model):
    registration = models.ForeignKey(
        "examination.Registration",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkin_logs",
    )
    exam = models.ForeignKey(
        "examination.Exam",
        on_delete=models.CASCADE,
        related_name="checkin_logs",
    )
    matched = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    attempted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-attempted_at"]

    def __str__(self):
        student = self.registration.full_name if self.registration else "Unknown"
        result = "GRANTED" if self.matched else "DENIED"
        return f"{result} — {student} — {self.exam.title}"


class ExamSession(models.Model):
    registration = models.ForeignKey(
        "examination.Registration",
        on_delete=models.CASCADE,
        related_name="exam_sessions",
    )
    exam = models.ForeignKey(
        "examination.Exam",
        on_delete=models.CASCADE,
        related_name="exam_sessions",
    )
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session — {self.registration.full_name} — {self.exam.title}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at