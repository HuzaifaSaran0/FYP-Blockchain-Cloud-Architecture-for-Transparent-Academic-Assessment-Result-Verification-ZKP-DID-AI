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
