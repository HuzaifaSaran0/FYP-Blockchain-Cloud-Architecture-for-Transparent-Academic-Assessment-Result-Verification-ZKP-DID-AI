from django.db import models


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